from __future__ import annotations

from typing import ClassVar

import libcst as cst
from libcst import matchers as m
from libcst.codemod import CodemodContext, ContextAwareTransformer, SkipFile
from libcst.codemod.visitors import AddImportsVisitor
from libcst.metadata import QualifiedNameProvider

from .support import (
    MAIN_GUARD,
    PARAM_ANY,
    PLACEHOLDER,
    RETURN_ANY,
    RETURN_NONE,
    TYPEVAR_LIKE,
    TYPING_MODULES,
    import_module_name,
    make_all_list,
)


class StubTransformer(ContextAwareTransformer):
    """Transforms a Python source module into a .pyi stub in-place."""

    METADATA_DEPENDENCIES = (QualifiedNameProvider,)

    def __init__(self, context: CodemodContext, exported_names: frozenset[str] | None = None) -> None:
        super().__init__(context)
        self.exported_names = exported_names
        self.has_all_assign = False
        self.bare_typing_import = False
        self.class_depth = 0
        self.if_depth = 0
        self.overloads: dict[int, set[str]] = {}

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        if self.exported_names is not None and len(self.exported_names) == 0:
            raise SkipFile("Module has empty __all__")
        return tree.visit(self)

    @property
    def in_class(self) -> bool:
        return self.class_depth > 0

    @property
    def in_module_scope(self) -> bool:
        return not self.in_class and self.if_depth == 0

    def qname(self, node: cst.CSTNode) -> str | None:
        names = self.get_metadata(QualifiedNameProvider, node)
        if not names:
            return None
        return next(iter(names)).name

    def add_import(self, module: str, name: str) -> None:
        AddImportsVisitor.add_needed_import(self.context, module, name)

    def is_exported(self, name: str) -> bool:
        return self.exported_names is None or name in self.exported_names

    def has_overload(self, func: cst.FunctionDef) -> bool:
        return any(
            self.qname(dec.decorator) in {"typing.overload", "typing_extensions.overload"} for dec in func.decorators
        )

    @m.call_if_not_inside(m.Lambda())
    def leave_Param(self, original_node: cst.Param, updated_node: cst.Param) -> cst.Param:
        if updated_node.name.value in ("self", "cls"):
            return updated_node
        if updated_node.annotation is None:
            self.add_import("typing", "Any")
            updated_node = updated_node.with_changes(annotation=PARAM_ANY)
        if updated_node.default is not None:
            updated_node = updated_node.with_changes(default=cst.Ellipsis())
        return updated_node

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.BaseStatement | cst.RemovalSentinel:
        name = original_node.name.value

        if self.has_overload(original_node):
            self.overloads.setdefault(self.class_depth, set()).add(name)
        elif name in self.overloads.get(self.class_depth, set()):
            return cst.RemoveFromParent()

        if not self.in_class and not self.is_exported(name):
            return cst.RemoveFromParent()

        if updated_node.returns is None:
            if updated_node.name.value == "__init__":
                updated_node = updated_node.with_changes(returns=RETURN_NONE)
            else:
                self.add_import("typing", "Any")
                updated_node = updated_node.with_changes(returns=RETURN_ANY)
        return updated_node.with_changes(body=cst.SimpleStatementSuite(body=[cst.Expr(value=cst.Ellipsis())]))

    def visit_ClassDef(self, node: cst.ClassDef) -> bool:
        self.class_depth += 1
        return True

    def leave_ClassDef(
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.BaseStatement | cst.RemovalSentinel:
        self.overloads.pop(self.class_depth, None)
        self.class_depth -= 1

        if not self.in_class and not self.is_exported(original_node.name.value):
            return cst.RemoveFromParent()

        if isinstance(updated_node.body, cst.IndentedBlock) and not any(
            s for s in updated_node.body.body if not m.matches(s, PLACEHOLDER)
        ):
            return updated_node.with_changes(
                body=cst.IndentedBlock(
                    body=[cst.SimpleStatementLine(body=[cst.Expr(value=cst.Ellipsis())])],
                )
            )
        return updated_node

    STMT_HANDLERS: ClassVar[dict[type, str]] = {
        cst.AnnAssign: "handle_ann_assign",
        cst.Assign: "handle_assign",
        cst.AugAssign: "handle_aug_assign",
        cst.Import: "handle_import",
        cst.ImportFrom: "handle_import_from",
    }

    def leave_SimpleStatementLine(
        self,
        original_node: cst.SimpleStatementLine,
        updated_node: cst.SimpleStatementLine,
    ) -> cst.BaseStatement | cst.RemovalSentinel:
        orig = original_node.body[0]
        upd = updated_node.body[0]

        if isinstance(orig, cst.Pass) or (isinstance(orig, cst.Expr) and isinstance(orig.value, cst.Ellipsis)):
            return updated_node

        handler_name = self.STMT_HANDLERS.get(type(upd))
        if handler_name is not None:
            return getattr(self, handler_name)(updated_node, cst.ensure_type(orig, type(upd)), upd)

        return cst.RemoveFromParent()

    def handle_import_from(
        self,
        line: cst.SimpleStatementLine,
        orig: cst.ImportFrom,
        upd: cst.ImportFrom,
    ) -> cst.BaseStatement | cst.RemovalSentinel:
        if isinstance(upd.names, cst.ImportStar) or import_module_name(upd) == "__future__":
            return cst.RemoveFromParent()
        if self.exported_names is not None and self.in_module_scope:
            return self.apply_reexport(line, upd, self.exported_names)
        return line

    def handle_import(
        self,
        line: cst.SimpleStatementLine,
        orig: cst.Import,
        upd: cst.Import,
    ) -> cst.BaseStatement | cst.RemovalSentinel:
        if not isinstance(upd.names, (list, tuple)):
            return cst.RemoveFromParent()

        if any(isinstance(alias.name, cst.Name) and alias.name.value in TYPING_MODULES for alias in upd.names):
            self.bare_typing_import = True

        filtered = [
            alias
            for alias in upd.names
            if not (isinstance(alias.name, cst.Name) and alias.name.value in TYPING_MODULES)
        ]
        if not filtered:
            return line
        if len(filtered) < len(upd.names):
            return line.with_changes(body=[upd.with_changes(names=filtered)])
        return line

    def handle_ann_assign(
        self,
        line: cst.SimpleStatementLine,
        orig: cst.AnnAssign,
        upd: cst.AnnAssign,
    ) -> cst.BaseStatement | cst.RemovalSentinel:
        if self.in_module_scope and isinstance(upd.target, cst.Name) and not self.is_exported(upd.target.value):
            return cst.RemoveFromParent()
        if upd.value is not None:
            return line.with_changes(body=[upd.with_changes(value=cst.Ellipsis())])
        return line

    def handle_assign(
        self,
        line: cst.SimpleStatementLine,
        orig: cst.Assign,
        upd: cst.Assign,
    ) -> cst.BaseStatement | cst.RemovalSentinel:
        if self.in_class:
            return cst.RemoveFromParent()
        return self.transform_module_assign(line, orig, upd)

    def handle_aug_assign(
        self,
        line: cst.SimpleStatementLine,
        orig: cst.AugAssign,
        upd: cst.AugAssign,
    ) -> cst.BaseStatement | cst.RemovalSentinel:
        if not (isinstance(upd.target, cst.Name) and upd.target.value == "__all__"):
            return cst.RemoveFromParent()

        if self.has_all_assign:
            return cst.RemoveFromParent()
        self.has_all_assign = True

        if self.exported_names is not None:
            return cst.SimpleStatementLine(
                body=[
                    cst.Assign(
                        targets=[cst.AssignTarget(target=cst.Name("__all__"))],
                        value=make_all_list(self.exported_names),
                    )
                ]
            )
        return cst.RemoveFromParent()

    def apply_reexport(
        self,
        line: cst.SimpleStatementLine,
        imp: cst.ImportFrom,
        exported: frozenset[str],
    ) -> cst.SimpleStatementLine:
        if isinstance(imp.names, cst.ImportStar):
            return line
        mod = import_module_name(imp)
        if mod in TYPING_MODULES or mod == "__future__":
            return line
        new_names = list(imp.names)
        changed = False
        for i, alias in enumerate(new_names):
            if isinstance(alias.name, cst.Name) and alias.name.value in exported and alias.asname is None:
                new_names[i] = alias.with_changes(
                    asname=cst.AsName(
                        whitespace_before_as=cst.SimpleWhitespace(" "),
                        whitespace_after_as=cst.SimpleWhitespace(" "),
                        name=cst.Name(alias.name.value),
                    )
                )
                changed = True
        if changed:
            return line.with_changes(body=[imp.with_changes(names=new_names)])
        return line

    def transform_module_assign(
        self,
        line: cst.SimpleStatementLine,
        orig: cst.Assign,
        upd: cst.Assign,
    ) -> cst.BaseStatement | cst.RemovalSentinel:
        target_name: str | None = None
        if len(orig.targets) == 1 and isinstance(orig.targets[0].target, cst.Name):
            target_name = orig.targets[0].target.value

        if isinstance(orig.value, cst.Call) and isinstance(orig.value.func, cst.Name):
            func_name = orig.value.func.value
            qn = self.qname(orig.value.func)
            effective = qn.rsplit(".", 1)[-1] if qn else func_name
            if effective in TYPEVAR_LIKE:
                if target_name is not None and not self.is_exported(target_name):
                    return cst.RemoveFromParent()
                self.add_import("typing", effective)
                return line

        if not self.bare_typing_import:
            qn = self.qname(orig.value)
            if qn and any(qn.startswith(f"{mod}.") for mod in TYPING_MODULES):
                for target in orig.targets:
                    if isinstance(target.target, cst.Name):
                        if not self.is_exported(target.target.value):
                            return cst.RemoveFromParent()
                        return line.with_changes(
                            body=[
                                cst.AnnAssign(
                                    target=target.target,
                                    annotation=cst.Annotation(annotation=upd.value),
                                )
                            ]
                        )

        if target_name == "__all__":
            self.has_all_assign = True
            if self.exported_names is not None:
                return line.with_changes(body=[orig.with_changes(value=make_all_list(self.exported_names))])
            return line

        if target_name is not None and not self.is_exported(target_name):
            return cst.RemoveFromParent()

        return line

    def visit_If(self, node: cst.If) -> bool:
        self.if_depth += 1
        return True

    def leave_If(self, original_node: cst.If, updated_node: cst.If) -> cst.BaseStatement | cst.RemovalSentinel:
        self.if_depth -= 1
        if m.findall(original_node.test, MAIN_GUARD):
            return cst.RemoveFromParent()
        return updated_node

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        self.add_import("__future__", "annotations")
        body = list(updated_node.body)
        if body and hasattr(body[0], "leading_lines"):
            body[0] = body[0].with_changes(leading_lines=())
        return updated_node.with_changes(header=(), body=body)
