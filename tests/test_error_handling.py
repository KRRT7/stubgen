"""Tests for generator error handling.

Covers edge cases where ``generate_stub`` receives malformed or unusual
input: syntax errors, non-Python content, BOM, and ``# coding:`` declarations.
"""

import libcst
import pytest

from stubgen import generate_stub


class TestSyntaxErrors:
    def test_invalid_syntax_raises(self) -> None:
        with pytest.raises(libcst.ParserSyntaxError):
            generate_stub("def foo(: int) -> None: ...")

    def test_unterminated_string_raises(self) -> None:
        with pytest.raises(libcst.ParserSyntaxError):
            generate_stub("x = 'hello")

    def test_partial_truncated_code_raises(self) -> None:
        with pytest.raises(libcst.ParserSyntaxError):
            generate_stub("class Foo:\n    def bar(")


class TestNonPythonContent:
    def test_binary_junk_raises(self) -> None:
        with pytest.raises(libcst.ParserSyntaxError):
            generate_stub("\x00\x01\x02\x03\xff\xfe")

    def test_html_content_raises(self) -> None:
        with pytest.raises(libcst.ParserSyntaxError):
            generate_stub("<html><body>Hello</body></html>")


class TestBOMHandling:
    def test_utf8_bom_results_in_empty_stub(self) -> None:
        source = "\ufeff" + "\n"
        result = generate_stub(source)
        assert result == "from __future__ import annotations\n"

    def test_utf8_bom_with_code_strips_bom(self) -> None:
        source = "\ufeff" + "x: int = 42\n"
        result = generate_stub(source)
        assert "x: int" in result


class TestCodingDeclarations:
    def test_coding_comment_doesnt_break_generation(self) -> None:
        source = "# -*- coding: utf-8 -*-\nx: int\n"
        result = generate_stub(source)
        assert "x: int" in result

    def test_function_after_coding_declaration(self) -> None:
        source = "# coding: utf-8\ndef f() -> None: ...\n"
        result = generate_stub(source)
        assert "def f()" in result

    def test_encoding_cookie_doesnt_break_generation(self) -> None:
        source = "# vim: set fileencoding=utf-8 :\ndef f() -> None: ...\n"
        result = generate_stub(source)
        assert "def f()" in result


