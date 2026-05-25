from __future__ import annotations

from typing import Callable, Sequence

import libcst as cst
from libcst import matchers as m
from libcst.helpers import get_full_name_for_node

TYPING_MODULES = frozenset({"typing", "typing_extensions"})
TYPEVAR_LIKE = frozenset({"TypeVar", "ParamSpec", "TypeVarTuple"})

MAIN_GUARD = m.Comparison(
    left=m.Name("__name__"),
    comparisons=[
        m.ComparisonTarget(
            operator=m.Equal(),
            comparator=m.SimpleString(value='"__main__"') | m.SimpleString(value="'__main__'"),
        )
    ],
)

PLACEHOLDER = m.SimpleStatementLine(body=[m.Pass() | m.Expr(value=m.Ellipsis())])

PARAM_ANY = cst.Annotation(annotation=cst.Name("Any"))

RETURN_ANY = cst.Annotation(
    annotation=cst.Name("Any"),
    whitespace_before_indicator=cst.SimpleWhitespace(" "),
    whitespace_after_indicator=cst.SimpleWhitespace(" "),
)
RETURN_NONE = cst.Annotation(
    annotation=cst.Name("None"),
    whitespace_before_indicator=cst.SimpleWhitespace(" "),
    whitespace_after_indicator=cst.SimpleWhitespace(" "),
)


def evaluate_string(expr: cst.BaseExpression) -> str | None:
    """Return the string value of a static string expression, or None if dynamic."""
    if isinstance(expr, cst.SimpleString):
        val = expr.evaluated_value
        return val if isinstance(val, str) else None
    if isinstance(expr, cst.ConcatenatedString):
        left = evaluate_string(expr.left)
        right = evaluate_string(expr.right)
        return left + right if left is not None and right is not None else None
    return None


def collect_all_names(collection_expr: cst.BaseExpression) -> set[str] | None:
    """Return string literal names from a List/Tuple/Set, or None if dynamic.

    Handles static ``__all__`` definitions including ``+=``, ``.append()``,
    and ``.extend()`` — covering more cases than
    :class:`~libcst.codemod.visitors.GatherExportsVisitor`, which only tracks
    assignment and augmented assignment.
    """
    if not isinstance(collection_expr, (cst.List, cst.Tuple, cst.Set)):
        return None
    names: set[str] = set()
    for elt in collection_expr.elements:
        val = evaluate_string(elt.value)
        if val is None:
            return None
        names.add(val)
    return names


def extract_exported_names(module: cst.Module) -> frozenset[str] | None:
    accumulated: set[str] = set()
    found_any = False
    for stmt in module.body:
        if not isinstance(stmt, cst.SimpleStatementLine):
            continue
        body0 = stmt.body[0]

        if isinstance(body0, cst.Assign):
            if any(isinstance(t.target, cst.Name) and t.target.value == "__all__" for t in body0.targets):
                names = collect_all_names(body0.value)
                if names is not None:
                    accumulated |= names
                    found_any = True

        elif isinstance(body0, cst.AugAssign) and body0.operator.__class__ is cst.AddAssign:
            if isinstance(body0.target, cst.Name) and body0.target.value == "__all__":
                names = collect_all_names(body0.value)
                if names is not None:
                    accumulated |= names
                    found_any = True

        elif (
            isinstance(body0, cst.Expr)
            and isinstance(body0.value, cst.Call)
            and isinstance(body0.value.func, cst.Attribute)
            and isinstance(body0.value.func.value, cst.Name)
            and body0.value.func.value.value == "__all__"
        ):
            method = body0.value.func.attr.value
            call = body0.value
            if method == "extend" and len(call.args) == 1:
                names = collect_all_names(call.args[0].value)
                if names is not None:
                    accumulated |= names
                    found_any = True
            elif method == "append" and len(call.args) == 1:
                arg = call.args[0].value
                if isinstance(arg, cst.SimpleString) and isinstance(arg.evaluated_value, str):
                    accumulated.add(arg.evaluated_value)
                    found_any = True

    return frozenset(accumulated) if found_any else None


def import_module_name(imp: cst.ImportFrom) -> str:
    """Return the dotted module name for an ImportFrom node, or '' if relative."""
    if imp.relative or imp.module is None:
        return ""
    return get_full_name_for_node(imp.module) or ""


def import_local_name(alias: cst.ImportAlias) -> str:
    """Return the local name introduced by an import alias.

    Uses :attr:`ImportAlias.evaluated_alias` and
    :attr:`ImportAlias.evaluated_name` instead of manual tree walking.
    """
    if alias.evaluated_alias is not None:
        return alias.evaluated_alias
    name = alias.evaluated_name
    return name.split(".", 1)[0] if "." in name else name


def is_reexport(alias: cst.ImportAlias) -> bool:
    """Return True if the alias re-exports the same name (e.g. ``from X import Y as Y``)."""
    ea = alias.evaluated_alias
    return ea is not None and ea == alias.evaluated_name


def make_annotation(name: str) -> cst.Annotation:
    return cst.Annotation(
        annotation=cst.Name(name),
        whitespace_before_indicator=cst.SimpleWhitespace(" "),
        whitespace_after_indicator=cst.SimpleWhitespace(" "),
    )


def make_all_list(names: frozenset[str]) -> cst.List:
    return cst.List(
        elements=[cst.Element(value=cst.SimpleString(f'"{name}"')) for name in sorted(names)],
    )


class UsedNamesCollector(cst.CSTVisitor):
    """Collect Name values referenced outside of import statements.

    Unlike :class:`~libcst.codemod.visitors.GatherImportsVisitor`, which
    tracks what is *imported*, this visitor tracks what names are *used*
    in the code — skipping imported names so they can be pruned later.
    """

    def __init__(self) -> None:
        self.used: set[str] = set()

    def visit_ImportFrom(self, node: cst.ImportFrom) -> bool:
        return False

    def visit_Import(self, node: cst.Import) -> bool:
        return False

    def visit_Name(self, node: cst.Name) -> None:
        self.used.add(node.value)


class StubImportPruner(m.MatcherDecoratableTransformer):
    """Prune top-level imports that only supported removed implementation code."""

    def __init__(
        self,
        *,
        source_names: set[str],
        stub_names: set[str],
        exported_names: frozenset[str] | None,
    ) -> None:
        super().__init__()
        self.source_names = source_names
        self.stub_names = stub_names
        self.exported_names = exported_names

    def should_drop_alias(self, alias: cst.ImportAlias, module: str = "") -> bool:
        if is_reexport(alias):
            return False
        local = import_local_name(alias)
        if local in self.stub_names:
            return False
        if module in TYPING_MODULES:
            return True
        if self.exported_names is not None:
            return True
        return local in self.source_names

    def filter_aliases(
        self,
        aliases: Sequence[cst.ImportAlias],
        *,
        should_drop: Callable[[cst.ImportAlias], bool],
    ) -> list[cst.ImportAlias] | None:
        kept = [alias for alias in aliases if not should_drop(alias)]
        if not kept:
            return None
        if len(kept) < len(aliases):
            kept[-1] = kept[-1].with_changes(comma=cst.MaybeSentinel.DEFAULT)
        return kept

    @m.call_if_not_inside(m.IndentedBlock())
    def leave_SimpleStatementLine(
        self,
        original_node: cst.SimpleStatementLine,
        updated_node: cst.SimpleStatementLine,
    ) -> cst.BaseStatement | cst.RemovalSentinel:
        stmt = updated_node.body[0]

        if isinstance(stmt, cst.ImportFrom) and not isinstance(stmt.names, cst.ImportStar):
            module = import_module_name(stmt)
            if module == "__future__":
                return updated_node
            kept = self.filter_aliases(
                stmt.names,
                should_drop=lambda alias: self.should_drop_alias(alias, module),
            )
            if kept is None:
                return cst.RemoveFromParent()
            return updated_node.with_changes(body=[stmt.with_changes(names=kept)])

        if isinstance(stmt, cst.Import) and isinstance(stmt.names, (list, tuple)):
            kept = self.filter_aliases(
                stmt.names,
                should_drop=lambda alias: import_local_name(alias) not in self.stub_names,
            )
            if kept is None:
                return cst.RemoveFromParent()
            return updated_node.with_changes(body=[stmt.with_changes(names=kept)])

        return updated_node
