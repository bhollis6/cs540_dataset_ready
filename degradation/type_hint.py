import libcst as cst
import random
import glob

class TypeHintStripper(cst.CSTTransformer):
    def __init__(self, removal_chance=1):
        self.removal_chance = removal_chance
        self.hints_encountered = 0
        self.hints_removed = 0
        
        self.in_protected_class = False
        self.in_protected_function = False

        # Edge cases that shouldn't be degraded.
        self.protected_class_decorators = {"dataclass", "define", "type"} # dataclasses, attrs, strawberry
        self.protected_base_classes = {"BaseModel", "NamedTuple", "TypedDict", "Base", "DeclarativeBase"} # Pydantic, typing, SQLAlchemy
        self.protected_func_decorators = {
            "get", "post", "put", "delete", "patch", # FastAPI
            "command",                               # Typer CLI
            "singledispatch", "register",            # functools
            "beartype"                               # Runtime checkers
        }

    def _get_node_name(self, node):
        """Safely extracts the string name from various AST node types (Name, Attribute, Call)."""
        if isinstance(node, cst.Name):
            return node.value
        elif isinstance(node, cst.Attribute):
            return node.attr.value
        elif isinstance(node, cst.Call):
            return self._get_node_name(node.func)
        return None

    def visit_ClassDef(self, node: cst.ClassDef) -> bool:
        # Check decorators
        for dec in node.decorators:
            name = self._get_node_name(dec.decorator)
            if name in self.protected_class_decorators:
                self.in_protected_class = True
                return True

        # Check base classes (inheritance)
        for base in node.bases:
            name = self._get_node_name(base.value)
            if name in self.protected_base_classes:
                self.in_protected_class = True
                return True

        self.in_protected_class = False
        return True

    def leave_ClassDef(self, original_node, updated_node):
        self.in_protected_class = False
        return updated_node

    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:
        for dec in node.decorators:
            name = self._get_node_name(dec.decorator)
            if name in self.protected_func_decorators:
                self.in_protected_function = True
                return True
                    
        self.in_protected_function = False
        return True

    def leave_FunctionDef(self, original_node, updated_node):
        self.in_protected_function = False
        
        if original_node.returns and not self.in_protected_class and not self.in_protected_function:
            self.hints_encountered += 1
            if random.random() < self.removal_chance:
                self.hints_removed += 1
                return updated_node.with_changes(returns=None)
        return updated_node

    def leave_AnnAssign(self, original_node, updated_node):
        if self.in_protected_class or self.in_protected_function:
            return updated_node
            
        self.hints_encountered += 1 
        if random.random() < self.removal_chance:
            self.hints_removed += 1
            if updated_node.value is None:
                return cst.Pass()
            else:
                return cst.Assign(targets=[cst.AssignTarget(updated_node.target)], value=updated_node.value)
        return updated_node

    def leave_Param(self, original_node, updated_node):
        if self.in_protected_class or self.in_protected_function:
            return updated_node
            
        if original_node.annotation:
            self.hints_encountered += 1
            if random.random() < self.removal_chance:
                self.hints_removed += 1
                return updated_node.with_changes(annotation=None)
        return updated_node

def process_repo(repo_path):
    files = glob.glob(f"{repo_path}/**/*.py", recursive=True)
    
    total_hints_before = 0
    total_hints_removed = 0
    
    for file_path in files:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
            
        try:
            tree = cst.parse_module(source)
            transformer = TypeHintStripper(removal_chance=1)
            modified_tree = tree.visit(transformer)
            
            total_hints_before += transformer.hints_encountered
            total_hints_removed += transformer.hints_removed
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(modified_tree.code)
                
            print(f"Processed: {file_path} (Removed {transformer.hints_removed}/{transformer.hints_encountered} hints)")
        except Exception as e:
            print(f"Failed to process {file_path}: {e}")

    print(f"\nSummary: Removed {total_hints_removed} out of {total_hints_before} safe hints.")

# Insert repo directory here
process_repo("starlette")