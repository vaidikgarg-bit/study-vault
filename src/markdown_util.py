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


def get_word_frequency_distribution(text: str, top_n: int = 10) -> dict:
    """Calculates token distribution across substantive words."""
    if not text:
        return {}
    tokens = re.findall(r"\b[A-Za-z]{3,}\b", text.lower())
    freq = {}
    for t in tokens:
        freq[t] = freq.get(t, 0) + 1
    return dict(sorted(freq.items(), key=lambda x: x[1], reverse=True)[:top_n])


def extract_code_snippets(markdown_text: str) -> dict:
    """
    Extracts fenced code blocks (```lang ... ```) from markdown notes,
    identifying programming languages, line counts, and frequency distribution.
    """
    if not markdown_text:
        return {"total_snippets": 0, "languages": {}, "snippets": []}

    pattern = re.compile(r"```([a-zA-Z0-9_\-+]*)\n?(.*?)```", re.DOTALL)
    matches = pattern.findall(markdown_text)

    snippets = []
    lang_counts = {}

    for idx, (lang, code) in enumerate(matches, 1):
        language = lang.strip().lower() if lang.strip() else "plaintext"
        code_body = code.strip()
        lines = code_body.splitlines() if code_body else []
        lang_counts[language] = lang_counts.get(language, 0) + 1

        snippets.append({
            "index": idx,
            "language": language,
            "line_count": len(lines),
            "char_count": len(code_body),
            "code": code_body
        })

    return {
        "total_snippets": len(snippets),
        "languages": lang_counts,
        "snippets": snippets
    }


def generate_table_of_contents(markdown_text: str) -> list:
    """
    Parses Markdown headers (# to ####) and generates an anchor-linked Table of Contents structure.
    """
    if not markdown_text:
        return []

    toc = []
    pattern = re.compile(r"^\s*(#{1,4})\s+(.+)$", re.MULTILINE)
    for match in pattern.finditer(markdown_text):
        hashes, title = match.groups()
        level = len(hashes)
        clean_title = title.strip()
        anchor = re.sub(r"[^\w\s-]", "", clean_title.lower()).strip().replace(" ", "-")
        toc.append({
            "level": level,
            "title": clean_title,
            "anchor": f"#{anchor}"
        })

    return toc


def extract_markdown_links(markdown_text: str) -> list:
    """
    Extracts hyperlinked citations and references from markdown notes.
    Distinguishes external web URLs from internal anchor fragments.
    """
    if not markdown_text:
        return []

    pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    links = []
    for match in pattern.finditer(markdown_text):
        label, url = match.groups()
        label_clean = label.strip()
        url_clean = url.strip()
        is_external = url_clean.startswith(("http://", "https://"))
        links.append({
            "label": label_clean,
            "url": url_clean,
            "is_external": is_external
        })

    return links


