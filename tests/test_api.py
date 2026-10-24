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


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "timestamp" in data


def test_get_courses():
    response = client.get("/api/courses")
    assert response.status_code == 200
    courses = response.json()
    assert len(courses) >= 3
    codes = [c["code"] for c in courses]
    assert "CS101" in codes
    assert "MATH200" in codes

    # Test course stats
    first_id = courses[0]["id"]
    stats_res = client.get(f"/api/courses/{first_id}/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert "total_notes" in stats
    assert "total_words" in stats
    assert "unique_topics" in stats


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

    course_id = data["id"]
    # Update course
    update_res = client.put(f"/api/courses/{course_id}", json={"title": "Advanced Molecular Genetics", "color": "emerald"})
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "Advanced Molecular Genetics"
    assert update_res.json()["color"] == "emerald"

    # Delete course
    del_res = client.delete(f"/api/courses/{course_id}")
    assert del_res.status_code == 200


def test_get_notes():
    response = client.get("/api/notes")
    assert response.status_code == 200
    notes = response.json()
    assert len(notes) >= 3


def test_search_notes():
    # Search for BST or tree
    res = client.get("/api/notes?search=BST")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1
    assert "BST" in data[0]["title"] or "BST" in data[0]["content"]

    # Search with no match
    res_empty = client.get("/api/notes?search=NonExistentSubjectXYZ123")
    assert res_empty.status_code == 200
    assert len(res_empty.json()) == 0

    # Filter by favorite_only
    fav_res = client.get("/api/notes?favorite_only=true")
    assert fav_res.status_code == 200
    assert isinstance(fav_res.json(), list)

    # Filter by tag
    tag_res = client.get("/api/notes?tag=trees")
    assert tag_res.status_code == 200
    assert isinstance(tag_res.json(), list)


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


def test_update_note():
    notes = client.get("/api/notes").json()
    note_id = notes[0]["id"]

    update_payload = {
        "title": "Updated BST & Balanced Trees",
        "tags": "trees,binary-search,avl"
    }
    response = client.put(f"/api/notes/{note_id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated BST & Balanced Trees"
    assert "trees" in data["tags"]


def test_toggle_note_favorite():
    notes = client.get("/api/notes").json()
    note_id = notes[0]["id"]

    # Toggle favorite on
    res1 = client.post(f"/api/notes/{note_id}/favorite")
    assert res1.status_code == 200
    assert res1.json()["id"] == note_id
    assert res1.json()["is_favorite"] is True

    # Toggle favorite off
    res2 = client.post(f"/api/notes/{note_id}/favorite")
    assert res2.status_code == 200
    assert res2.json()["is_favorite"] is False


def test_export_note_markdown_and_json():
    notes = client.get("/api/notes").json()
    note_id = notes[0]["id"]

    res_md = client.get(f"/api/notes/{note_id}/export/markdown")
    assert res_md.status_code == 200
    assert "text/markdown" in res_md.headers["content-type"]
    assert "# " in res_md.text

    res_json = client.get(f"/api/notes/{note_id}/export/json")
    assert res_json.status_code == 200
    assert "application/json" in res_json.headers["content-type"]
    data = res_json.json()
    assert data["id"] == note_id
    assert "course" in data

    # Test text export
    res_txt = client.get(f"/api/notes/{note_id}/export/txt")
    assert res_txt.status_code == 200
    assert "text/plain" in res_txt.headers["content-type"]
    assert "TITLE:" in res_txt.text


def test_note_summary():
    notes = client.get("/api/notes").json()
    note_id = notes[0]["id"]
    res = client.get(f"/api/notes/{note_id}/summary")
    assert res.status_code == 200
    data = res.json()
    assert "summary_bullets" in data
    assert len(data["summary_bullets"]) > 0


def test_get_note_concepts():
    notes = client.get("/api/notes").json()
    note_id = notes[0]["id"]
    res = client.get(f"/api/notes/{note_id}/concepts")
    assert res.status_code == 200
    data = res.json()
    assert "concepts" in data
    assert len(data["concepts"]) > 0
    assert "relevance_score" in data["concepts"][0]


def test_cloze_flashcards():
    notes = client.get("/api/notes").json()
    note_id = notes[0]["id"]
    res = client.post(f"/api/notes/{note_id}/cloze-cards")
    assert res.status_code == 200
    data = res.json()
    assert "cloze_cards" in data
    assert len(data["cloze_cards"]) > 0
    assert "[ ... ]" in data["cloze_cards"][0]["front"]


def test_regenerate_quiz():
    notes = client.get("/api/notes").json()
    note_id = notes[0]["id"]
    # First generate
    res1 = client.post(f"/api/notes/{note_id}/quiz")
    assert res1.status_code == 200

    # Regenerate
    res2 = client.post(f"/api/notes/{note_id}/quiz/regenerate")
    assert res2.status_code == 200
    assert len(res2.json()["questions"]) > 0


def test_duplicate_note():
    notes = client.get("/api/notes").json()
    orig = notes[0]
    res = client.post(f"/api/notes/{orig['id']}/duplicate")
    assert res.status_code == 201
    copy_note = res.json()
    assert copy_note["id"] != orig["id"]
    assert f"{orig['title']} (Copy)" == copy_note["title"]
    assert copy_note["course_id"] == orig["course_id"]


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

    # Test due flashcard decks queue
    due_res = client.get("/api/flashcards/due")
    assert due_res.status_code == 200
    assert "total_decks" in due_res.json()
    assert due_res.json()["total_decks"] >= 1


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

    # Test single attempt detail
    attempt_id = data["id"]
    att_detail = client.get(f"/api/quiz-attempts/{attempt_id}")
    assert att_detail.status_code == 200
    assert att_detail.json()["id"] == attempt_id
    assert "note_title" in att_detail.json()

    # Verify analytics update
    analytics_res = client.get("/api/analytics")
    assert analytics_res.status_code == 200
    analytics = analytics_res.json()
    assert analytics["quizzes_taken"] >= 1
    assert analytics["average_score_percent"] > 0

    # Test study activity timeline
    activity_res = client.get("/api/analytics/activity")
    assert activity_res.status_code == 200
    act_data = activity_res.json()
    assert "recent_attempts" in act_data
    assert "daily_breakdown" in act_data
    assert "current_streak_days" in act_data
    assert len(act_data["recent_attempts"]) >= 1


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


def test_pin_note_and_ordering():
    notes = client.get("/api/notes").json()
    note_id = notes[0]["id"]
    res1 = client.post(f"/api/notes/{note_id}/pin")
    assert res1.status_code == 200
    assert res1.json()["is_pinned"] is True
    # Verify pinned note is first
    ordered = client.get("/api/notes").json()
    assert ordered[0]["id"] == note_id
    assert ordered[0]["is_pinned"] is True
    # Unpin
    res2 = client.post(f"/api/notes/{note_id}/pin")
    assert res2.status_code == 200
    assert res2.json()["is_pinned"] is False
