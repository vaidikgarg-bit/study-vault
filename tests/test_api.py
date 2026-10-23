"""
Automated unit and integration test suite for StudyVault API.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

# Add src to module search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from app import app
from database import init_db

# Initialize database
init_db()
client = TestClient(app)


def test_get_courses():
    response = client.get("/api/courses")
    assert response.status_code == 200
    courses = response.json()
    assert len(courses) >= 3
    codes = [c["code"] for c in courses]
    assert "CS101" in codes
    assert "MATH200" in codes


def test_create_course():
    import random
    rnd = random.randint(100, 999)
    payload = {
        "code": f"BIO{rnd}",
        "title": "Molecular Biology & Genetics",
        "department": "Biological Sciences",
        "color": "rose"
    }
    response = client.post("/api/courses", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == f"BIO{rnd}"
    assert data["title"] == "Molecular Biology & Genetics"


def test_get_notes():
    response = client.get("/api/notes")
    assert response.status_code == 200
    notes = response.json()
    assert len(notes) >= 3


def test_create_note():
    # Fetch first course id
    courses = client.get("/api/courses").json()
    course_id = courses[0]["id"]

    payload = {
        "course_id": course_id,
        "title": "Asymptotic Notations: Big-O, Big-Omega, Big-Theta",
        "topic": "Algorithm Analysis",
        "content": """Big-O Notation: Represents the tight mathematical upper bound of an algorithm.
Big-Omega Notation: Represents the lower bound (best-case scenario).
Big-Theta Notation: Represents an asymptotically tight bound where both upper and lower bounds coincide.
Constant Time: O(1) algorithms execute in fixed time regardless of input size."""
    }
    response = client.post("/api/notes", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert "id" in data


def test_upload_pdf_note():
    from pdf_parser import create_sample_pdf_bytes
    courses = client.get("/api/courses").json()
    course_id = courses[0]["id"]
    pdf_bytes = create_sample_pdf_bytes("Slide Deck", "Operating Systems Overview")

    files = {"file": ("lecture1.pdf", pdf_bytes, "application/pdf")}
    data = {
        "course_id": str(course_id),
        "title": "Operating Systems Virtual Memory Slide Deck",
        "topic": "Virtual Memory"
    }
    response = client.post("/api/notes/upload-pdf", data=data, files=files)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["title"] == data["title"]
    assert "id" in res_data


def test_generate_quiz():
    # Get note id
    notes = client.get("/api/notes").json()
    note_id = notes[0]["id"]

    response = client.post(f"/api/notes/{note_id}/quiz")
    assert response.status_code == 200
    data = response.json()
    assert "questions" in data
    assert len(data["questions"]) >= 1

    q = data["questions"][0]
    assert "question" in q
    assert len(q["options"]) == 4
    assert 0 <= q["correct_index"] < 4
    assert "explanation" in q


def test_generate_flashcards():
    notes = client.get("/api/notes").json()
    note_id = notes[0]["id"]

    response = client.post(f"/api/notes/{note_id}/flashcards")
    assert response.status_code == 200
    data = response.json()
    assert "flashcards" in data
    assert len(data["flashcards"]) >= 1

    card = data["flashcards"][0]
    assert "front" in card
    assert "back" in card


def test_record_quiz_attempt_and_analytics():
    notes = client.get("/api/notes").json()
    note_id = notes[0]["id"]

    payload = {
        "note_id": note_id,
        "score": 4,
        "total_questions": 5,
        "time_taken_seconds": 45
    }
    response = client.post("/api/quiz-attempts", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["score"] == 4
    assert data["percentage"] == 80.0

    # Verify analytics update
    analytics_res = client.get("/api/analytics")
    assert analytics_res.status_code == 200
    analytics = analytics_res.json()
    assert analytics["quizzes_taken"] >= 1
    assert analytics["average_score_percent"] > 0


def test_analytics_counts_generated_flashcards():
    before = client.get("/api/analytics").json()["total_flashcards"]
    note_res = client.post("/api/notes", json={
        "course_id": client.get("/api/courses").json()[0]["id"],
        "title": "Hash Tables",
        "topic": "Hashing",
        "content": "Load Factor: number of stored entries divided by bucket count.\nChaining: each bucket holds a linked list of colliding entries."
    })
    note_id = note_res.json()["id"]
    cards = client.post(f"/api/notes/{note_id}/flashcards").json()["flashcards"]

    after = client.get("/api/analytics").json()["total_flashcards"]
    assert after - before == len(cards)


@pytest.mark.parametrize("score, total, seconds", [
    (6, 5, 30),   # score above total
    (-1, 5, 30),  # negative score
    (0, 0, 30),   # zero questions
    (3, 5, -10),  # negative time
])
def test_record_quiz_attempt_rejects_invalid_values(score, total, seconds):
    note_id = client.get("/api/notes").json()[0]["id"]
    response = client.post("/api/quiz-attempts", json={
        "note_id": note_id,
        "score": score,
        "total_questions": total,
        "time_taken_seconds": seconds
    })
    assert response.status_code == 422


def test_record_quiz_attempt_for_missing_note_returns_404():
    response = client.post("/api/quiz-attempts", json={
        "note_id": 999999,
        "score": 1,
        "total_questions": 2,
        "time_taken_seconds": 10
    })
    assert response.status_code == 404


def test_delete_note():
    # Create temporary note to delete
    courses = client.get("/api/courses").json()
    course_id = courses[0]["id"]
    note_res = client.post("/api/notes", json={
        "course_id": course_id,
        "title": "Temporary Note to Delete",
        "topic": "Test Topic",
        "content": "This note will be safely deleted in tests."
    })
    note_id = note_res.json()["id"]

    del_res = client.delete(f"/api/notes/{note_id}")
    assert del_res.status_code == 200

    # Ensure it's deleted
    get_res = client.get(f"/api/notes/{note_id}")
    assert get_res.status_code == 404
