"""
Markdown utility helpers for sanitizing user note content and stripping syntax.
"""

import re


def strip_markdown_formatting(text: str) -> str:
    """
    Strips Markdown styling (headers, bold, italics, links, backticks)
    returning clean plain text.
    """
    if not text:
        return ""

    # Remove headers (# Title)
    cleaned = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Remove bold/italics (***, **, *, __, _)
    cleaned = re.sub(r"(\*{1,3}|_{1,3})(.*?)\1", r"\2", cleaned)
    # Remove inline code (`code`)
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
    # Remove links [text](url) -> text
    cleaned = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", cleaned)
    # Remove blockquotes (> quote)
    cleaned = re.sub(r"^>\s+", "", cleaned, flags=re.MULTILINE)
    # Remove horizontal rules
    cleaned = re.sub(r"^[-*_]{3,}\s*$", "", cleaned, flags=re.MULTILINE)

    return cleaned.strip()


def sanitize_markdown(text: str) -> str:
    """
    Escapes dangerous HTML tags (<script>, <iframe>, <object>, <embed>, <applet>)
    to protect notes from XSS injection while keeping legitimate LaTeX / math unharmed.
    """
    if not text:
        return ""

    dangerous_tags = [r"<\s*script[^>]*>.*?<\s*/\s*script\s*>",
                      r"<\s*iframe[^>]*>.*?<\s*/\s*iframe\s*>",
                      r"<\s*object[^>]*>.*?<\s*/\s*object\s*>",
                      r"<\s*embed[^>]*>",
                      r"<\s*applet[^>]*>.*?<\s*/\s*applet\s*>"]

    cleaned = text
    for pattern in dangerous_tags:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.DOTALL)

    return cleaned
