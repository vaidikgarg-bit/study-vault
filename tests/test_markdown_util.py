"""
Unit tests for markdown stripping and sanitization utility.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from markdown_util import strip_markdown_formatting, sanitize_markdown


def test_strip_markdown_headers_and_bold():
    raw = "# Main Heading\n\nThis is **bold** and *italic* text."
    stripped = strip_markdown_formatting(raw)
    assert "#" not in stripped
    assert "**" not in stripped
    assert "Main Heading" in stripped
    assert "bold and italic text." in stripped


def test_strip_markdown_code_and_links():
    raw = "Check [`binary_search()`](https://example.com) for details."
    stripped = strip_markdown_formatting(raw)
    assert "`" not in stripped
    assert "https://example.com" not in stripped
    assert "binary_search()" in stripped


def test_sanitize_markdown_removes_scripts():
    raw = "Normal text <script>alert('xss')</script> and math $x = y^2$."
    sanitized = sanitize_markdown(raw)
    assert "<script>" not in sanitized
    assert "alert" not in sanitized
    assert "math $x = y^2$" in sanitized


def test_sanitize_markdown_handles_empty():
    assert sanitize_markdown("") == ""
    assert strip_markdown_formatting("") == ""


def test_word_frequency_distribution():
    text = "binary tree search binary algorithm tree search"
    dist = get_word_frequency_distribution(text, top_n=3)
    assert dist["binary"] == 2
    assert dist["tree"] == 2
    assert dist["search"] == 2
