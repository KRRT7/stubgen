from __future__ import annotations

import importlib.util
from pathlib import Path

import libcst as cst
from libcst.codemod import Codemod, CodemodContext, SkipFile
from libcst.codemod.visitors import AddImportsVisitor

from .engine import StubTransformer
from .support import StubImportPruner, UsedNamesCollector, extract_exported_names

vendored_stubgen_path = Path(__file__).resolve().parent.parent / "vendored" / "stubgen" / "stubgen.py"


def load_vendored_stubgen():
    """Import the vendored AST-based stubgen via file-location spec.

    On Python 3.9+ the vendored file uses ``ast.unparse`` (stdlib) so
    no sibling modules are needed — we load it directly.
    """
    spec = importlib.util.spec_from_file_location("nuitka_stubgen.vendored_stubgen_imported", vendored_stubgen_path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fallback_generate(source_code: str) -> str | None:
    """Generate a stub using the vendored AST-based generator.

    Returns ``None`` when the fallback also fails.
    """
    import types  # noqa: PLC0415

    try:
        stubgen = load_vendored_stubgen()
        if not isinstance(stubgen, types.ModuleType):
            return None
        result = stubgen.generate_stub_from_source(source_code, output_file_path=None, text_only=True)
        return result.rstrip() + "\n"
    except Exception:  # noqa: BLE001  # deliberate safety net
        return None


class StubGenerationCodemod(Codemod):
    """Coordinate stub rewriting, import insertion, and import pruning."""

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        exported = extract_exported_names(tree)
        stub = self.apply_transformer(tree, exported)
        return self.inject_and_prune(tree, stub, exported)

    def apply_transformer(self, tree: cst.Module, exported: frozenset[str] | None) -> cst.Module:
        try:
            return StubTransformer(self.context, exported).transform_module(tree)
        except SkipFile:
            AddImportsVisitor.add_needed_import(self.context, "__future__", "annotations")
            return AddImportsVisitor(self.context).transform_module(cst.Module(body=[]))

    def inject_and_prune(
        self,
        source_tree: cst.Module,
        stub: cst.Module,
        exported: frozenset[str] | None,
    ) -> cst.Module:
        source_names = UsedNamesCollector()
        source_tree.visit(source_names)

        stub = stub.visit(AddImportsVisitor(self.context))

        stub_names = UsedNamesCollector()
        stub.visit(stub_names)

        return stub.visit(
            StubImportPruner(
                source_names=source_names.used,
                stub_names=stub_names.used,
                exported_names=exported,
            )
        )


def generate_stub(source_code: str) -> str:
    try:
        module = cst.parse_module(source_code)
        code = StubGenerationCodemod(CodemodContext()).transform_module(module).code
        return code.rstrip() + "\n"
    except Exception:
        fallback = fallback_generate(source_code)
        if fallback is not None:
            return fallback
        raise


def write_stub(source_file_path: str | Path, output_file_path: str | Path) -> None:
    source = Path(source_file_path).read_text(encoding="utf-8")
    Path(output_file_path).write_text(generate_stub(source), encoding="utf-8")
