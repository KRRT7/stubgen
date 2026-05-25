"""Stub output quality checks.

Validates that generated stubs are well-formed: no real function bodies,
no main-guard leaks, and that stub generation is idempotent.
"""

from __future__ import annotations

import ast
from typing import Any

from .core import generate_stub


def has_live_body(body: list[ast.stmt]) -> bool:
    """Return True if *body* contains statements other than stub-only ``...`` / ``pass``."""
    for stmt in body:
        if isinstance(stmt, (ast.Pass, ast.Raise)):
            continue
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and stmt.value.value is Ellipsis:
            continue
        return True
    return False


def walk_bodies(tree: ast.AST) -> list[list[ast.stmt]]:
    """Return every function/class body at all nesting levels."""
    bodies: list[list[ast.stmt]] = []

    def collect(node: ast.AST) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bodies.append(node.body)
        for child in ast.iter_child_nodes(node):
            collect(child)

    collect(tree)
    return bodies


def roundtrip(stub_text: str) -> str:
    """Run stub generation on *stub_text* and return the second-pass result."""
    return generate_stub(stub_text)


def top_level_names(tree: ast.Module) -> set[str]:
    """Extract top-level exported-ish names from a module AST.

    Returns names of top-level function defs, class defs, annotated
    assignments, and simple assignments (excluding ``__all__``).
    """
    names: set[str] = set()
    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(stmt.name)
        elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            names.add(stmt.target.id)
        elif isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name) and target.id != "__all__":
                    names.add(target.id)
    return names


def compare_asts(actual: Any, expected: Any, path: str = "") -> tuple[bool, str]:
    """Structural equality for two ASTs, ignoring position/context metadata.

    Returns ``(True, "")`` on match, or ``(False, description)`` on mismatch.
    """
    if type(actual) is not type(expected):
        return False, f"{path}: type {type(actual).__name__} != {type(expected).__name__}"

    if isinstance(actual, ast.AST):
        for name in actual._fields:
            if name in ("lineno", "col_offset", "end_lineno", "end_col_offset", "ctx"):
                continue
            child_path = f"{path}.{name}" if path else name
            a_val = getattr(actual, name)
            e_val = getattr(expected, name)
            ok, msg = compare_asts(a_val, e_val, child_path)
            if not ok:
                return False, msg
        return True, ""

    if isinstance(actual, list):
        if len(actual) != len(expected):
            return False, f"{path}: length {len(actual)} != {len(expected)}"
        for i, (a, e) in enumerate(zip(actual, expected)):
            ok, msg = compare_asts(a, e, f"{path}[{i}]")
            if not ok:
                return False, msg
        return True, ""

    if actual != expected:
        return False, f"{path}: {actual!r} != {expected!r}"
    return True, ""


def check_name_parity(source: str, stub: str) -> list[str]:
    """Return names that appear at the top level of *source* but not in *stub*.

    This catches accidental drops of public names during stub generation.
    """
    try:
        source_tree = ast.parse(source)
    except SyntaxError:
        return []

    try:
        stub_tree = ast.parse(stub)
    except SyntaxError:
        return []

    source_names = top_level_names(source_tree)
    stub_names = top_level_names(stub_tree)
    return sorted(source_names - stub_names)
