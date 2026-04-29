"""Conservative type-hint stripping for targeted pilot workspaces."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import libcst as cst


PROTECTED_CLASS_DECORATORS = {
    "dataclass",
    "define",
    "type",
    "s",
    "attrs",
    "frozen",
    "as_declarative",
}
PROTECTED_BASE_CLASSES = {
    "BaseModel",
    "NamedTuple",
    "TypedDict",
    "Base",
    "DeclarativeBase",
    "Protocol",
    "Generic",
    "Enum",
    "IntEnum",
    "StrEnum",
    "BaseSettings",
    "RootModel",
    "SQLModel",
    "MappedAsDataclass",
}
PROTECTED_FUNC_DECORATORS = {
    "get",
    "post",
    "put",
    "delete",
    "patch",
    "command",
    "group",
    "option",
    "argument",
    "singledispatch",
    "register",
    "overload",
    "given",
    "fixture",
    "model_validator",
    "field_validator",
}


def _node_name(node: cst.CSTNode) -> str | None:
    if isinstance(node, cst.Name):
        return node.value
    if isinstance(node, cst.Attribute):
        return node.attr.value
    if isinstance(node, cst.Call):
        return _node_name(node.func)
    return None


@dataclass
class TypeHintStripStats:
    hints_encountered: int = 0
    hints_removed: int = 0


class TypeHintStripper(cst.CSTTransformer):
    """Strip annotations while preserving runtime-sensitive typed structures."""

    def __init__(self) -> None:
        self.stats = TypeHintStripStats()
        self._class_protection_stack: list[bool] = []
        self._func_protection_stack: list[bool] = []

    @property
    def _is_protected(self) -> bool:
        return any(self._class_protection_stack) or any(self._func_protection_stack)

    def visit_ClassDef(self, node: cst.ClassDef) -> bool:
        protected = any(
            _node_name(decorator.decorator) in PROTECTED_CLASS_DECORATORS
            for decorator in node.decorators
        )
        if not protected:
            protected = any(_node_name(base.value) in PROTECTED_BASE_CLASSES for base in node.bases)
        self._class_protection_stack.append(protected)
        return True

    def leave_ClassDef(
        self,
        original_node: cst.ClassDef,
        updated_node: cst.ClassDef,
    ) -> cst.ClassDef:
        self._class_protection_stack.pop()
        return updated_node

    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:
        protected = any(
            _node_name(decorator.decorator) in PROTECTED_FUNC_DECORATORS
            for decorator in node.decorators
        )
        self._func_protection_stack.append(protected)
        return True

    def leave_FunctionDef(
        self,
        original_node: cst.FunctionDef,
        updated_node: cst.FunctionDef,
    ) -> cst.FunctionDef:
        self._func_protection_stack.pop()
        if original_node.name.value.startswith("__") and original_node.name.value.endswith("__"):
            return updated_node
        if original_node.returns is None or self._is_protected:
            return updated_node
        self.stats.hints_encountered += 1
        self.stats.hints_removed += 1
        return updated_node.with_changes(returns=None)

    def leave_Param(self, original_node: cst.Param, updated_node: cst.Param) -> cst.Param:
        if original_node.annotation is None or self._is_protected:
            return updated_node
        self.stats.hints_encountered += 1
        self.stats.hints_removed += 1
        return updated_node.with_changes(annotation=None)

    def leave_AnnAssign(
        self,
        original_node: cst.AnnAssign,
        updated_node: cst.AnnAssign,
    ) -> cst.BaseSmallStatement:
        if self._is_protected:
            return updated_node
        self.stats.hints_encountered += 1
        self.stats.hints_removed += 1
        if updated_node.value is None:
            return cst.Pass()
        return cst.Assign(
            targets=[cst.AssignTarget(updated_node.target)],
            value=updated_node.value,
        )


def strip_type_hints(source: str) -> tuple[str, TypeHintStripStats]:
    tree = cst.parse_module(source)
    transformer = TypeHintStripper()
    modified = tree.visit(transformer)
    return modified.code, transformer.stats


def process_file(path: Path) -> TypeHintStripStats:
    source = path.read_text(encoding="utf-8")
    transformed, stats = strip_type_hints(source)
    path.write_text(transformed, encoding="utf-8")
    return stats
