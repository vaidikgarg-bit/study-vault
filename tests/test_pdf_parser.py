"""
Unit tests for PDF document text extraction service.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from pdf_parser import extract_text_from_pdf_bytes, create_sample_pdf_bytes


def test_pdf_extraction_valid_doc():
    sample_bytes = create_sample_pdf_bytes("Lecture 1", "Introduction to Algorithms")
    result = extract_text_from_pdf_bytes(sample_bytes)
    assert result["page_count"] == 1
    assert "content" in result
