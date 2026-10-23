"""
FastAPI Server for StudyVault: Course Notes Hub & AI Quiz Generator.
"""

import json
import os
import sys

# Ensure src/ directory is on module search path when imported by uvicorn
sys.path.insert(0, os.path.dirname(__file__))

from typing import List
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from database import init_db, get_db_connection
from models import (
    CourseCreate, CourseResponse,
    NoteCreate, NoteResponse,
    QuizGenerateResponse, FlashcardsResponse,
    QuizAttemptCreate, QuizAttemptResponse,
    AnalyticsResponse
)
from ai_generator import generate_quiz_from_notes, generate_flashcards_from_notes

# Initialize DB tables on startup
init_db()

app = FastAPI(
    title="StudyVault API",
    description="Course Notes Hub and AI-Powered Quiz & Flashcard Study Engine",
    version="1.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def serve_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "StudyVault API is running. Visit /docs for interactive Swagger UI."}


# ---------------------------------------------------------------------------
# Courses Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/courses", response_model=List[CourseResponse])
def get_courses():
    conn = get_db_connection()
    rows = conn.execute("""
    SELECT c.*, COUNT(n.id) as note_count
    FROM courses c
    LEFT JOIN notes n ON c.id = n.course_id
    GROUP BY c.id
    ORDER BY c.code ASC;
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/api/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(course: CourseCreate):
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO courses (code, title, department, color) VALUES (?, ?, ?, ?) RETURNING id, created_at;",
            (course.code.upper().strip(), course.title.strip(), course.department.strip(), course.color or "indigo")
        )
        row = cursor.fetchone()
        conn.commit()
        course_id, created_at = row["id"], row["created_at"]
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Course code already exists or invalid data: {str(e)}")
    conn.close()
    return {
        "id": course_id,
        "code": course.code.upper().strip(),
        "title": course.title.strip(),
        "department": course.department.strip(),
        "color": course.color or "indigo",
        "note_count": 0,
        "created_at": str(created_at)
    }


# ---------------------------------------------------------------------------
# Notes Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/courses/{course_id}/notes", response_model=List[NoteResponse])
def get_course_notes(course_id: int):
    conn = get_db_connection()
    rows = conn.execute("""
    SELECT n.*, c.code as course_code, c.title as course_title
    FROM notes n
    JOIN courses c ON n.course_id = c.id
    WHERE n.course_id = ?
    ORDER BY n.created_at DESC;
    """, (course_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/notes", response_model=List[NoteResponse])
def get_all_notes():
    conn = get_db_connection()
    rows = conn.execute("""
    SELECT n.*, c.code as course_code, c.title as course_title
    FROM notes n
    JOIN courses c ON n.course_id = c.id
    ORDER BY n.created_at DESC;
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/notes/{note_id}", response_model=NoteResponse)
def get_single_note(note_id: int):
    conn = get_db_connection()
    row = conn.execute("""
    SELECT n.*, c.code as course_code, c.title as course_title
    FROM notes n
    JOIN courses c ON n.course_id = c.id
    WHERE n.id = ?;
    """, (note_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Note not found")
    return dict(row)


@app.post("/api/notes", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
def create_note(note: NoteCreate):
    conn = get_db_connection()
    course = conn.execute("SELECT code, title FROM courses WHERE id = ?;", (note.course_id,)).fetchone()
    if not course:
        conn.close()
        raise HTTPException(status_code=404, detail="Course not found")

    cursor = conn.execute(
        "INSERT INTO notes (course_id, title, topic, content) VALUES (?, ?, ?, ?) RETURNING id, created_at;",
        (note.course_id, note.title.strip(), note.topic.strip(), note.content.strip())
    )
    row = cursor.fetchone()
    conn.commit()
    note_id, created_at = row["id"], row["created_at"]
    conn.close()

    return {
        "id": note_id,
        "course_id": note.course_id,
        "course_code": course["code"],
        "course_title": course["title"],
        "title": note.title.strip(),
        "topic": note.topic.strip(),
        "content": note.content.strip(),
        "created_at": str(created_at)
    }


@app.delete("/api/notes/{note_id}")
def delete_note(note_id: int):
    conn = get_db_connection()
    cursor = conn.execute("DELETE FROM notes WHERE id = ?;", (note_id,))
    conn.commit()
    conn.close()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"message": "Note deleted successfully"}


# ---------------------------------------------------------------------------
# AI Quiz & Flashcard Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/notes/{note_id}/quiz", response_model=QuizGenerateResponse)
def generate_or_get_quiz(note_id: int):
    conn = get_db_connection()
    note = conn.execute("SELECT id, title, content FROM notes WHERE id = ?;", (note_id,)).fetchone()
    if not note:
        conn.close()
        raise HTTPException(status_code=404, detail="Note not found")

    # Check cache
    cached = conn.execute("SELECT questions_json FROM quizzes WHERE note_id = ?;", (note_id,)).fetchone()
    if cached:
        questions = json.loads(cached["questions_json"])
        conn.close()
        return {"note_id": note_id, "note_title": note["title"], "questions": questions}

    # Generate fresh quiz
    questions = generate_quiz_from_notes(note["title"], note["content"])
    conn.execute(
        "INSERT OR REPLACE INTO quizzes (note_id, questions_json) VALUES (?, ?);",
        (note_id, json.dumps(questions))
    )
    conn.commit()
    conn.close()

    return {"note_id": note_id, "note_title": note["title"], "questions": questions}


@app.post("/api/notes/{note_id}/flashcards", response_model=FlashcardsResponse)
def generate_or_get_flashcards(note_id: int):
    conn = get_db_connection()
    note = conn.execute("SELECT id, title, content FROM notes WHERE id = ?;", (note_id,)).fetchone()
    if not note:
        conn.close()
        raise HTTPException(status_code=404, detail="Note not found")

    # Check cache
    cached = conn.execute("SELECT cards_json FROM flashcards WHERE note_id = ?;", (note_id,)).fetchone()
    if cached:
        cards = json.loads(cached["cards_json"])
        conn.close()
        return {"note_id": note_id, "note_title": note["title"], "flashcards": cards}

    # Generate fresh flashcards
    cards = generate_flashcards_from_notes(note["title"], note["content"])
    conn.execute(
        "INSERT OR REPLACE INTO flashcards (note_id, cards_json) VALUES (?, ?);",
        (note_id, json.dumps(cards))
    )
    conn.commit()
    conn.close()

    return {"note_id": note_id, "note_title": note["title"], "flashcards": cards}


# ---------------------------------------------------------------------------
# Quiz Attempts & Analytics Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/quiz-attempts", response_model=QuizAttemptResponse, status_code=status.HTTP_201_CREATED)
def record_quiz_attempt(attempt: QuizAttemptCreate):
    conn = get_db_connection()
    cursor = conn.execute(
        "INSERT INTO quiz_attempts (note_id, score, total_questions, time_taken_seconds) VALUES (?, ?, ?, ?) RETURNING id, created_at;",
        (attempt.note_id, attempt.score, attempt.total_questions, attempt.time_taken_seconds)
    )
    row = cursor.fetchone()
    conn.commit()
    attempt_id, created_at = row["id"], row["created_at"]
    conn.close()

    pct = round((attempt.score / max(1, attempt.total_questions)) * 100, 1)
    return {
        "id": attempt_id,
        "note_id": attempt.note_id,
        "score": attempt.score,
        "total_questions": attempt.total_questions,
        "time_taken_seconds": attempt.time_taken_seconds,
        "percentage": pct,
        "created_at": str(created_at)
    }


@app.get("/api/analytics", response_model=AnalyticsResponse)
def get_analytics():
    conn = get_db_connection()
    total_courses = conn.execute("SELECT COUNT(*) FROM courses;").fetchone()[0]
    total_notes = conn.execute("SELECT COUNT(*) FROM notes;").fetchone()[0]

    attempts = conn.execute("""
    SELECT COUNT(*) as count, AVG(CAST(score AS FLOAT) / total_questions) as avg_score
    FROM quiz_attempts;
    """).fetchone()

    quizzes_taken = attempts["count"] or 0
    avg_score_raw = attempts["avg_score"] or 0.0
    avg_score_percent = round(avg_score_raw * 100, 1)

    cards_count = conn.execute("SELECT COUNT(*) FROM flashcards;").fetchone()[0]
    conn.close()

    return {
        "total_courses": total_courses,
        "total_notes": total_notes,
        "quizzes_taken": quizzes_taken,
        "average_score_percent": avg_score_percent,
        "total_flashcards_reviewed": cards_count * 6  # Estimated reviewed
    }
