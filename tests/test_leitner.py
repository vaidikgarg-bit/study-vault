"""
Unit and integration tests for Leitner 5-Box Spaced Repetition engine and API.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from app import app
from leitner import calculate_leitner_transition, LEITNER_BOX_INTERVALS

client = TestClient(app)


def test_leitner_transition_success():
    res1 = calculate_leitner_transition(current_box=1, recalled_successfully=True)
    assert res1["new_box"] == 2
    assert res1["interval_days"] == 2

    res4 = calculate_leitner_transition(current_box=4, recalled_successfully=True)
    assert res4["new_box"] == 5
    assert res4["interval_days"] == 14

    # Max box capped at 5
    res5 = calculate_leitner_transition(current_box=5, recalled_successfully=True)
    assert res5["new_box"] == 5


def test_leitner_transition_failure():
    # Failed card in Box 4 resets to Box 1
    res = calculate_leitner_transition(current_box=4, recalled_successfully=False)
    assert res["new_box"] == 1
    assert res["interval_days"] == 1


def test_leitner_api_endpoints():
    notes = client.get("/api/notes").json()
    note_id = notes[0]["id"]

    # Review card 1 successfully
    res_move = client.post(f"/api/flashcards/{note_id}/leitner/review", json={
        "card_id": 1,
        "current_box": 1,
        "recalled_successfully": True
    })
    assert res_move.status_code == 200
    data = res_move.json()
    assert data["new_box"] == 2

    # Get boxes summary
    res_boxes = client.get(f"/api/flashcards/{note_id}/leitner/boxes")
    assert res_boxes.status_code == 200
    boxes = res_boxes.json()
    assert len(boxes) == 5
    assert any(b["box"] == 2 and b["card_count"] >= 1 for b in boxes)
