import tokenize
import io
import os
import argparse
import ast
from pathlib import Path

# Added 'tests' and 'test' to the exclusion list
EXCLUDE_DIRS = {'.git', 'venv', 'env', '__pycache__', '.tox', 'build', 'dist', '.idea', '.vscode', 'tests', 'test', 'testing'}
PRAGMAS = ('noqa', 'type:', 'pylint:', 'fmt:', 'mypy:', 'pyright:', 'coding:')

def is_structurally_identical(source_original: str, source_stripped: str) -> bool:
    class StructuralNodeVisitor(ast.NodeVisitor):
        def __init__(self):
            self.nodes = []

        def generic_visit(self, node):
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                return
            self.nodes.append(type(node).__name__)
            super().generic_visit(node)

    try:
        tree_orig = ast.parse(source_original)
        tree_stripped = ast.parse(source_stripped)

        visitor_orig = StructuralNodeVisitor()
        visitor_orig.visit(tree_orig)

        visitor_stripped = StructuralNodeVisitor()
        visitor_stripped.visit(tree_stripped)

        return visitor_orig.nodes == visitor_stripped.nodes
    except Exception as e:
        return False


def process_file(filepath: Path) -> bool:
    temp_filepath = None
    try:
        with open(filepath, 'rb') as f:
            source_bytes = f.read()

        source_text = source_bytes.decode('utf-8')
        tokens = list(tokenize.tokenize(io.BytesIO(source_bytes).readline))
        cleaned_tokens = []
        
        nesting_depth = 0

        for i, tok in enumerate(tokens):
            if tok.type == tokenize.OP:
                if tok.string in '([{':
                    nesting_depth += 1
                elif tok.string in ')]}':
                    nesting_depth = max(0, nesting_depth - 1)
                    
            if tok.type == tokenize.COMMENT:
                if (tok.start[0] == 1 and tok.string.startswith('#!')) or any(p in tok.string.lower() for p in PRAGMAS):
                    cleaned_tokens.append(tok)
                continue
                
            elif tok.type == tokenize.STRING or getattr(tok, 'type', None) == getattr(tokenize, 'FSTRING_START', None):
                if nesting_depth > 0:
                    cleaned_tokens.append(tok)
                    continue

                prev_tok = tokens[i-1] if i > 0 else None
                next_tok = tokens[i+1] if i < len(tokens)-1 else None
                
                if prev_tok and prev_tok.type == tokenize.NL:
                    tok_minus_2 = tokens[i-2] if i > 1 else None
                    if tok_minus_2 and tok_minus_2.type in (tokenize.STRING, getattr(tokenize, 'FSTRING_END', None)):
                        cleaned_tokens.append(tok)
                        continue

                if prev_tok and prev_tok.type == tokenize.OP and prev_tok.string == ':':
                    cleaned_tokens.append(tok)
                    continue

                valid_prev = prev_tok and prev_tok.type in (tokenize.INDENT, tokenize.DEDENT, tokenize.NEWLINE, tokenize.NL, tokenize.ENCODING)
                valid_next = next_tok and next_tok.type in (tokenize.NEWLINE, tokenize.NL, tokenize.ENDMARKER)
                
                if valid_prev and valid_next:
                    new_tok = tokenize.TokenInfo(
                        tokenize.STRING,
                        '""',
                        tok.start,
                        tok.end,
                        tok.line
                    )
                    cleaned_tokens.append(new_tok)
                    
                    if getattr(tok, 'type', None) == getattr(tokenize, 'FSTRING_START', None):
                        pass
                else:
                    cleaned_tokens.append(tok)
                    
            else:
                cleaned_tokens.append(tok)

        clean_source_bytes = tokenize.untokenize(cleaned_tokens)
        clean_source_text = clean_source_bytes.decode('utf-8')

        if not is_structurally_identical(source_text, clean_source_text):
            print(f"[!] Structural mismatch detected in {filepath}. Reverting file.")
            return False

        temp_filepath = filepath.with_name(filepath.name + ".tmp")
        with open(temp_filepath, 'wb') as f:
            f.write(clean_source_bytes)
            f.flush()
            os.fsync(f.fileno())
            
        os.replace(temp_filepath, filepath)
        return True

    except Exception as e:
        print(f"[!] Error processing {filepath}: {e}")
        if temp_filepath and temp_filepath.exists():
            temp_filepath.unlink()
        return False

def strip_comments_docstrings(directory):
    target_path = Path(directory)
    if not target_path.is_dir():
        print(f"Error: {directory} is not a valid directory.")
        return

    processed_count = 0
    failed_count = 0

    for root, dirs, files in os.walk(target_path):
        # Exclude designated directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            # Skip test files explicitly
            if file.endswith('.py') and not file.startswith('test_') and not file.endswith('_test.py'):
                filepath = Path(root) / file
                if process_file(filepath):
                    processed_count += 1
                    print(f"Cleaned: {filepath}")
                else:
                    failed_count += 1

    print(f"\nDone.")
    print(f"Successfully stripped: {processed_count} files.")
    if failed_count > 0:
        print(f"Skipped (Safety Reverts/Errors): {failed_count} files.")

if __name__ == "__main__":
    import sys
    # Allow passing directory via CLI, default to current dir if none provided
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    strip_comments_docstrings(r"starlette")