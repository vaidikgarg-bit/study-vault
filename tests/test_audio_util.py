"""
Unit tests for text-to-speech audio sentence chunking and /api/notes/{id}/speech-chunks.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from app import app
from audio_util import chunk_note_for_speech

client = TestClient(app)


def test_chunk_note_for_speech():
    text = (
        "A Binary Search Tree is an efficient data structure. "
        "It maintains nodes in sorted order. "
        "Search, insertion, and deletion operations take logarithmic time on average."
    )
    chunks = chunk_note_for_speech(text, max_words_per_chunk=15)
    assert len(chunks) >= 2
    assert chunks[0]["chunk_index"] == 1
    assert chunks[0]["start_time_offset"] == 0.0
    assert chunks[0]["estimated_duration_seconds"] > 0
    # Next chunk starts where previous ends
    assert chunks[1]["start_time_offset"] == chunks[0]["estimated_duration_seconds"]


def test_chunk_note_empty():
    assert chunk_note_for_speech("") == []
    assert chunk_note_for_speech("   ") == []


def test_speech_chunks_endpoint():
    notes = client.get("/api/notes").json()
    note_id = notes[0]["id"]

    res = client.get(f"/api/notes/{note_id}/speech-chunks")
    assert res.status_code == 200
    data = res.json()
    assert data["note_id"] == note_id
    assert data["total_chunks"] >= 1
    assert data["total_audio_seconds"] > 0
    assert len(data["chunks"]) == data["total_chunks"]
