"""
Unit and integration tests for Anki exporter, parser, and flashcard import API.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from app import app
from anki_util import serialize_cards_to_anki, parse_anki_tsv

client = TestClient(app)


def test_anki_serializer_and_parser():
    cards = [
        {"front": "What is an AVL Tree?", "back": "A self-balancing BST.", "topic": "Trees"},
        {"front": "Line 1\nLine 2", "back": "Answer\nWith\nNewlines", "topic": "Syntax"}
    ]
    tsv = serialize_cards_to_anki(cards, deck_name="CS101::Trees")
    assert "#deck:CS101::Trees" in tsv
    assert "What is an AVL Tree?\tA self-balancing BST.\tTrees" in tsv
    assert "Line 1<br>Line 2\tAnswer<br>With<br>Newlines\tSyntax" in tsv

    # Parse back
    parsed = parse_anki_tsv(tsv)
    assert len(parsed) == 2
    assert parsed[0]["front"] == "What is an AVL Tree?"
    assert parsed[0]["back"] == "A self-balancing BST."
    assert parsed[0]["topic"] == "Trees"
    assert parsed[1]["front"] == "Line 1\nLine 2"


def test_anki_export_endpoint():
    notes = client.get("/api/notes").json()
    note_id = notes[0]["id"]
    res = client.get(f"/api/notes/{note_id}/export/anki")
    assert res.status_code == 200
    assert "text/tab-separated-values" in res.headers["content-type"]
    assert "#separator:tab" in res.text
    assert "#deck:" in res.text


def test_flashcard_import_endpoint():
    notes = client.get("/api/notes").json()
    note_id = notes[0]["id"]
    payload = {
        "cards": [
            {"front": "Custom Question 1", "back": "Custom Answer 1", "topic": "Custom"},
            {"front": "Custom Question 2", "back": "Custom Answer 2", "topic": "Custom"}
        ],
        "replace_existing": False
    }
    res = client.post(f"/api/notes/{note_id}/import/flashcards", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["imported_count"] == 2
    assert data["total_cards"] >= 2
