from __future__ import annotations

from pathlib import Path

import libcst as cst
from libcst.codemod import Codemod, CodemodContext, SkipFile
from libcst.codemod.visitors import AddImportsVisitor

from .engine import StubTransformer
from .support import StubImportPruner, UsedNamesCollector, extract_exported_names


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
    module = cst.parse_module(source_code)
    code = StubGenerationCodemod(CodemodContext()).transform_module(module).code
    return code.rstrip() + "\n"


def write_stub(source_file_path: str | Path, output_file_path: str | Path) -> None:
    source = Path(source_file_path).read_text(encoding="utf-8")
    Path(output_file_path).write_text(generate_stub(source), encoding="utf-8")
