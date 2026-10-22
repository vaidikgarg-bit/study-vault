"""
Unit tests for markdown stripping and sanitization utility.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from markdown_util import (
    strip_markdown_formatting,
    sanitize_markdown,
    get_word_frequency_distribution,
    extract_code_snippets,
    generate_table_of_contents,
    extract_markdown_links
)


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


def test_extract_code_snippets():
    md = """
    Here is some Python:
    ```python
    def hello():
        print("world")
    ```
    And some SQL:
    ```sql
    SELECT * FROM courses;
    ```
    And plaintext:
    ```
    unspecified language
    ```
    """
    res = extract_code_snippets(md)
    assert res["total_snippets"] == 3
    assert res["languages"]["python"] == 1
    assert res["languages"]["sql"] == 1
    assert res["languages"]["plaintext"] == 1
    assert res["snippets"][0]["language"] == "python"
    assert "print(\"world\")" in res["snippets"][0]["code"]
    assert res["snippets"][0]["line_count"] == 2


def test_generate_table_of_contents():
    md = """
    # Course Introduction
    Overview text.
    ## Module 1: Basics
    Subtopic details.
    ### Setup Instructions
    Steps.
    """
    toc = generate_table_of_contents(md)
    assert len(toc) == 3
    assert toc[0]["level"] == 1
    assert toc[0]["title"] == "Course Introduction"
    assert toc[0]["anchor"] == "#course-introduction"
    assert toc[1]["level"] == 2
    assert toc[2]["level"] == 3


def test_extract_markdown_links():
    md = """
    Check [FastAPI Docs](https://fastapi.tiangolo.com) or [Local Section](#setup).
    """
    links = extract_markdown_links(md)
    assert len(links) == 2
    assert links[0]["label"] == "FastAPI Docs"
    assert links[0]["url"] == "https://fastapi.tiangolo.com"
    assert links[0]["is_external"] is True
    assert links[1]["is_external"] is False


