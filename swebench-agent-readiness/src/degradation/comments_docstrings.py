"""Strip comments and docstrings while preserving runtime behavior."""

from __future__ import annotations

import ast
import io
import tokenize
from pathlib import Path


def _docstring_spans(tree: ast.AST) -> set[tuple[int, int, int, int]]:
    spans: set[tuple[int, int, int, int]] = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not isinstance(body, list) or not body:
            continue
        first_stmt = body[0]
        if not isinstance(first_stmt, ast.Expr):
            continue
        value = first_stmt.value
        if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
            continue
        if (
            first_stmt.lineno is None
            or first_stmt.end_lineno is None
            or first_stmt.col_offset is None
            or first_stmt.end_col_offset is None
        ):
            continue
        spans.add(
            (
                first_stmt.lineno,
                first_stmt.col_offset,
                first_stmt.end_lineno,
                first_stmt.end_col_offset,
            )
        )
    return spans


def _preserve_comment(token: tokenize.TokenInfo) -> bool:
    if token.start[0] == 1 and token.string.startswith("#!"):
        return True
    if token.start[0] <= 2 and "coding" in token.string:
        return True
    return False


def strip_comments_and_docstrings(source: str) -> str:
    """Return source with comments and docstrings removed."""

    tree = ast.parse(source)
    docstring_spans = _docstring_spans(tree)
    output_tokens: list[tokenize.TokenInfo] = []
    reader = io.StringIO(source).readline
    for token in tokenize.generate_tokens(reader):
        span = (*token.start, *token.end)
        if token.type == tokenize.STRING and span in docstring_spans:
            continue
        if token.type == tokenize.COMMENT and not _preserve_comment(token):
            continue
        output_tokens.append(token)

    transformed = tokenize.untokenize(output_tokens)
    if source.endswith("\n") and not transformed.endswith("\n"):
        transformed += "\n"
    return transformed


def process_file(path: Path) -> bool:
    """Rewrite a Python file in place. Returns True when content changed."""

    original = path.read_text(encoding="utf-8")
    transformed = strip_comments_and_docstrings(original)
    if transformed == original:
        return False
    path.write_text(transformed, encoding="utf-8")
    return True
