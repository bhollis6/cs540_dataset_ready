import libcst as cst
import random
import sys
from pathlib import Path


EXCLUDE_DIR_NAMES = {
    ".git", "venv", "env", ".venv", "__pycache__", ".tox", ".nox",
    "build", "dist", ".idea", ".vscode",
}

class SuperSafeTypeHintStripper(cst.CSTTransformer):
    def __init__(self, removal_chance=1.0):
        self.removal_chance = removal_chance
        self.hints_encountered = 0
        self.hints_removed = 0
        
        self.class_protection_stack = []
        self.func_protection_stack = []

        # Expanded to protect attrs, pydantic, dataclasses, and ORMs
        self.protected_class_decorators = {
            "dataclass", "define", "type", "s", "attrs", "frozen",
            "pydantic.dataclasses.dataclass", "as_declarative"
        }
        
        # Expanded to protect Settings, RootModels, and SQL structural models
        self.protected_base_classes = {
            "BaseModel", "NamedTuple", "TypedDict", "Base", "DeclarativeBase",
            "Protocol", "Generic", "Enum", "IntEnum", "StrEnum",
            "BaseSettings", "RootModel", "SQLModel", "MappedAsDataclass" 
        }
        
        # Expanded to protect API routers, CLI tools, and test frameworks
        self.protected_func_decorators = {
            "get", "post", "put", "delete", "patch",        # FastAPI/Flask
            "command", "group", "option", "argument",       # Typer/Click
            "singledispatch", "register", "beartype",       # Standard/Runtime
            "overload", "given", "fixture", "model_validator", "field_validator"
        }

    def _get_node_name(self, node):
        if isinstance(node, cst.Name):
            return node.value
        elif isinstance(node, cst.Attribute):
            return node.attr.value
        elif isinstance(node, cst.Call):
            return self._get_node_name(node.func)
        return None

    @property
    def is_protected(self):
        return any(self.class_protection_stack) or any(self.func_protection_stack)

    def visit_ClassDef(self, node: cst.ClassDef) -> bool:
        protected = False
        for dec in node.decorators:
            if self._get_node_name(dec.decorator) in self.protected_class_decorators:
                protected = True
                break

        if not protected:
            for base in node.bases:
                if self._get_node_name(base.value) in self.protected_base_classes:
                    protected = True
                    break

        self.class_protection_stack.append(protected)
        return True

    def leave_ClassDef(self, original_node, updated_node):
        self.class_protection_stack.pop()
        return updated_node

    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:
        protected = False
        for dec in node.decorators:
            if self._get_node_name(dec.decorator) in self.protected_func_decorators:
                protected = True
                break
                
        self.func_protection_stack.append(protected)
        return True

    def leave_FunctionDef(self, original_node, updated_node):
        self.func_protection_stack.pop()
        
        # Protect all dunder methods (like __init__, __init_subclass__) to avoid AST corruption
        if original_node.name.value.startswith("__") and original_node.name.value.endswith("__"):
             return updated_node

        if original_node.returns and not self.is_protected:
            self.hints_encountered += 1
            if random.random() < self.removal_chance:
                self.hints_removed += 1
                return updated_node.with_changes(returns=None)
        return updated_node

    def leave_AnnAssign(self, original_node, updated_node):
        if self.is_protected:
            return updated_node
            
        self.hints_encountered += 1 
        if random.random() < self.removal_chance:
            self.hints_removed += 1
            if updated_node.value is None:
                return cst.Pass()
            else:
                return cst.Assign(
                    targets=[cst.AssignTarget(updated_node.target)], 
                    value=updated_node.value
                )
        return updated_node

    def leave_Param(self, original_node, updated_node):
        if self.is_protected:
            return updated_node
            
        if original_node.annotation:
            self.hints_encountered += 1
            if random.random() < self.removal_chance:
                self.hints_removed += 1
                return updated_node.with_changes(annotation=None)
        return updated_node

def _should_skip_file(file_path: Path, repo_root: Path, skip_tests: bool) -> bool:
    relative_parts = file_path.relative_to(repo_root).parts
    if any(part in EXCLUDE_DIR_NAMES for part in relative_parts[:-1]):
        return True

    if not skip_tests:
        return False

    name = file_path.name.lower()
    return (
        name == "conftest.py"
        or name.startswith("test_")
        or name.endswith("_test.py")
        or any(part in {"tests", "test", "testing"} for part in relative_parts[:-1])
    )


def process_repo(repo_path, skip_tests=False):
    repo_root = Path(repo_path).resolve()
    files = [path for path in repo_root.rglob("*.py") if path.is_file()]
    
    total_hints_before = 0
    total_hints_removed = 0
    
    for file_path in files:
        if _should_skip_file(file_path, repo_root, skip_tests):
            continue
            
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
            
        try:
            tree = cst.parse_module(source)
            transformer = SuperSafeTypeHintStripper(removal_chance=1.0)
            modified_tree = tree.visit(transformer)
            
            total_hints_before += transformer.hints_encountered
            total_hints_removed += transformer.hints_removed
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(modified_tree.code)
                
        except Exception as e:
                print(f"Failed to process {file_path}: {e}")

    print(f"\nSummary: Removed {total_hints_removed} out of {total_hints_before} safe hints.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <repo_path>")
        sys.exit(1)
        
    target = sys.argv[1]
    process_repo(target, skip_tests=False)
