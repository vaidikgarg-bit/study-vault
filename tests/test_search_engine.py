"""
Unit and integration tests for search relevance scoring engine and /api/search endpoint.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from app import app
from search_engine import score_note_relevance, rank_notes

client = TestClient(app)


def test_score_note_relevance_title_exact_match():
    note = {
        "title": "Binary Search Trees",
        "topic": "Trees",
        "tags": "bst,data-structures",
        "content": "A binary search tree is a fast tree."
    }
    score = score_note_relevance("Binary Search Trees", note)
    # Exact title match gets 10.0 + token points
    assert score >= 14.0


def test_rank_notes_order():
    notes = [
        {"id": 1, "title": "Other Topic", "topic": "General", "content": "Just a small mention of trees."},
        {"id": 2, "title": "Binary Trees and Heaps", "topic": "Trees", "content": "Tree traversals and binary search."}
    ]
    ranked = rank_notes("Binary Trees", notes)
    assert len(ranked) >= 1
    assert ranked[0]["id"] == 2
    assert ranked[0]["relevance_score"] > 5.0


def test_api_search_endpoint():
    res = client.get("/api/search?q=Binary+Search")
    assert res.status_code == 200
    data = res.json()
    assert data["query"] == "Binary Search"
    assert data["total_matches"] >= 1
    assert "relevance_score" in data["results"][0]
    assert data["results"][0]["relevance_score"] > 0
