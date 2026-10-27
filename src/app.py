"""
FastAPI Server for StudyVault: Course Notes Hub & AI Quiz Generator.
"""

import json
import math
import os
import sys

# Ensure src/ directory is on module search path when imported by uvicorn
sys.path.insert(0, os.path.dirname(__file__))

from typing import List, Optional
from fastapi import FastAPI, HTTPException, status, UploadFile, File, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from datetime import datetime, timezone
from config import APP_NAME, APP_TITLE, APP_DESCRIPTION, APP_VERSION
from database import init_db, get_db_connection
from markdown_util import strip_markdown_formatting, sanitize_markdown, extract_code_snippets
from anki_util import serialize_cards_to_anki, parse_anki_tsv
from pdf_parser import extract_text_from_pdf_bytes
from gamification import evaluate_badges
from spaced_repetition import calculate_sm2, estimate_retention_probability, classify_card_urgency, project_retention_curve
from models import (
    CourseCreate, CourseResponse, CourseUpdate, CourseArchiveResponse,
    NoteCreate, NoteResponse, NoteUpdate, FavoriteToggleResponse,
    QuizGenerateResponse, FlashcardsResponse,
    QuizAttemptCreate, QuizAttemptResponse,
    AnalyticsResponse, HealthResponse,
    BulkDeleteRequest, BulkDeleteResponse,
    TagCount,
    StudySessionCreate,
    NoteHistoryResponse, NoteRevertResponse,
    FlashcardImportRequest, FlashcardImportResponse,
    StudySessionSummary, CourseFocusStats
)
from ai_generator import (
    generate_quiz_from_notes,
    generate_flashcards_from_notes,
    generate_cloze_flashcards,
    extract_key_concepts,
    extract_bullet_summary,
    calculate_readability_score,
    extract_definitions_and_takeaways
)

# Initialize DB tables on startup
init_db()

app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION
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


@app.get("/api/health", response_model=HealthResponse, tags=["System"])
def check_health():
    """System health check endpoint verifying database connectivity."""
    db_status = "connected"
    try:
        conn = get_db_connection()
        conn.execute("SELECT 1;").fetchone()
        conn.close()
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "app": APP_NAME,
        "version": APP_VERSION,
        "database": db_status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# ---------------------------------------------------------------------------
# Courses Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/courses", response_model=List[CourseResponse])
def get_courses(include_archived: bool = True):
    conn = get_db_connection()
    where_clause = "" if include_archived else "WHERE c.is_archived = 0"
    rows = conn.execute(f"""
    SELECT c.*, COUNT(n.id) as note_count
    FROM courses c
    LEFT JOIN notes n ON c.id = n.course_id
    {where_clause}
    GROUP BY c.id
    ORDER BY c.code ASC;
    """).fetchall()
    conn.close()
    return [{**dict(r), "is_archived": bool(r["is_archived"])} for r in rows]


@app.post("/api/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(course: CourseCreate):
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO courses (code, title, department, color, instructor, term, is_archived) VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING id, created_at;",
            (course.code.upper().strip(), course.title.strip(), course.department.strip(), course.color or "indigo", course.instructor or "", course.term or "Fall 2026", int(bool(course.is_archived)))
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
        "instructor": course.instructor or "",
        "term": course.term or "Fall 2026",
        "is_archived": bool(course.is_archived),
        "note_count": 0,
        "created_at": str(created_at)
    }


@app.put("/api/courses/{course_id}", response_model=CourseResponse)
def update_course(course_id: int, course_update: CourseUpdate):
    """Updates course title, department, theme color, instructor, term, or archival status."""
    conn = get_db_connection()
    course = conn.execute("SELECT * FROM courses WHERE id = ?;", (course_id,)).fetchone()
    if not course:
        conn.close()
        raise HTTPException(status_code=404, detail="Course not found")

    new_title = course_update.title.strip() if course_update.title is not None else course["title"]
    new_dept = course_update.department.strip() if course_update.department is not None else course["department"]
    new_color = course_update.color.strip() if course_update.color is not None else course["color"]
    new_inst = course_update.instructor.strip() if course_update.instructor is not None else course["instructor"]
    new_term = course_update.term.strip() if course_update.term is not None else course["term"]
    new_arch = int(course_update.is_archived) if course_update.is_archived is not None else course["is_archived"]

    conn.execute(
        "UPDATE courses SET title = ?, department = ?, color = ?, instructor = ?, term = ?, is_archived = ? WHERE id = ?;",
        (new_title, new_dept, new_color, new_inst, new_term, new_arch, course_id)
    )
    conn.commit()

    count = conn.execute("SELECT COUNT(*) FROM notes WHERE course_id = ?;", (course_id,)).fetchone()[0]
    conn.close()

    return {
        "id": course_id,
        "code": course["code"],
        "title": new_title,
        "department": new_dept,
        "color": new_color,
        "instructor": new_inst,
        "term": new_term,
        "is_archived": bool(new_arch),
        "note_count": count,
        "created_at": str(course["created_at"])
    }


@app.post("/api/courses/{course_id}/archive", response_model=CourseArchiveResponse, tags=["Courses"])
def toggle_course_archive(course_id: int):
    """Toggles archival status of a course."""
    conn = get_db_connection()
    course = conn.execute("SELECT id, is_archived FROM courses WHERE id = ?;", (course_id,)).fetchone()
    if not course:
        conn.close()
        raise HTTPException(status_code=404, detail="Course not found")

    new_state = 0 if course["is_archived"] else 1
    conn.execute("UPDATE courses SET is_archived = ? WHERE id = ?;", (new_state, course_id))
    conn.commit()
    conn.close()

    return {
        "id": course_id,
        "is_archived": bool(new_state),
        "message": f"Course successfully {'archived' if new_state else 'restored'}"
    }


@app.delete("/api/courses/{course_id}")
def delete_course(course_id: int):
    """Deletes course and cascades deletion of notes, quizzes, and flashcards."""
    conn = get_db_connection()
    cursor = conn.execute("DELETE FROM courses WHERE id = ?;", (course_id,))
    conn.commit()
    conn.close()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"message": "Course deleted successfully"}


@app.get("/api/courses/{course_id}/stats")
def get_course_stats(course_id: int):
    """Calculates comprehensive learning and content statistics for a course."""
    conn = get_db_connection()
    course = conn.execute("SELECT * FROM courses WHERE id = ?;", (course_id,)).fetchone()
    if not course:
        conn.close()
        raise HTTPException(status_code=404, detail="Course not found")

    notes = conn.execute("SELECT id, topic, content FROM notes WHERE course_id = ?;", (course_id,)).fetchall()
    topics = sorted(list(set(n["topic"] for n in notes)))

    total_words = sum(len(n["content"].split()) for n in notes)
    est_reading_time = max(1, math.ceil(total_words / 200))

    note_ids = [n["id"] for n in notes]
    quiz_attempts_count = 0
    if note_ids:
        placeholders = ",".join("?" for _ in note_ids)
        row = conn.execute(
            f"SELECT COUNT(*) FROM quiz_attempts WHERE note_id IN ({placeholders});",
            note_ids
        ).fetchone()
        quiz_attempts_count = row[0]

    conn.close()

    return {
        "course_id": course_id,
        "code": course["code"],
        "title": course["title"],
        "total_notes": len(notes),
        "total_words": total_words,
        "estimated_reading_time_mins": est_reading_time,
        "unique_topics": topics,
        "quiz_attempts_taken": quiz_attempts_count
    }


# ---------------------------------------------------------------------------
# Notes Endpoints
# ---------------------------------------------------------------------------

def enrich_note_dict(row_dict: dict) -> dict:
    """Computes dynamic word count and estimated reading time for note responses."""
    content = row_dict.get("content", "")
    words = len(content.split()) if content else 0
    reading_time = max(1, math.ceil(words / 200))
    d = dict(row_dict)
    d["word_count"] = words
    d["reading_time_mins"] = reading_time
    d["readability_score"] = calculate_readability_score(content)["score"]
    return d


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
    return [enrich_note_dict(dict(r)) for r in rows]


@app.get("/api/notes", response_model=List[NoteResponse])
def get_all_notes(
    search: Optional[str] = None,
    course_id: Optional[int] = None,
    favorite_only: Optional[bool] = False,
    tag: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Retrieves notes with optional keyword search, course filter, and favorite filter."""
    conn = get_db_connection()
    conditions = []
    params = []

    if course_id is not None:
        conditions.append("n.course_id = ?")
        params.append(course_id)

    if favorite_only:
        conditions.append("n.is_favorite = 1")

    if tag:
        conditions.append("n.tags LIKE ?")
        params.append(f"%{tag.strip()}%")

    if search:
        term = f"%{search.strip()}%"
        conditions.append("(n.title LIKE ? OR n.topic LIKE ? OR n.content LIKE ? OR c.code LIKE ?)")
        params.extend([term, term, term, term])

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    query = f"""
    SELECT n.*, c.code as course_code, c.title as course_title
    FROM notes n
    JOIN courses c ON n.course_id = c.id
    {where_clause}
    ORDER BY n.is_pinned DESC, n.created_at DESC
    LIMIT ? OFFSET ?;
    """
    params.extend([limit, offset])

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [enrich_note_dict(dict(r)) for r in rows]


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
    return enrich_note_dict(dict(row))


@app.post("/api/notes/{note_id}/duplicate", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
def duplicate_note(note_id: int):
    """Duplicates an existing study note with a copy suffix."""
    conn = get_db_connection()
    note = conn.execute("""
    SELECT n.*, c.code as course_code, c.title as course_title
    FROM notes n
    JOIN courses c ON n.course_id = c.id
    WHERE n.id = ?;
    """, (note_id,)).fetchone()
    if not note:
        conn.close()
        raise HTTPException(status_code=404, detail="Note not found")

    new_title = f"{note['title']} (Copy)"
    cursor = conn.execute(
        "INSERT INTO notes (course_id, title, topic, content, tags) VALUES (?, ?, ?, ?, ?) RETURNING id, created_at;",
        (note["course_id"], new_title, note["topic"], note["content"], note["tags"] or "")
    )
    row = cursor.fetchone()
    conn.commit()
    new_id, created_at = row["id"], row["created_at"]
    conn.close()

    return enrich_note_dict({
        "id": new_id,
        "course_id": note["course_id"],
        "course_code": note["course_code"],
        "course_title": note["course_title"],
        "title": new_title,
        "topic": note["topic"],
        "content": note["content"],
        "tags": note["tags"] or "",
        "is_favorite": False,
        "created_at": str(created_at)
    })


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

    return enrich_note_dict({
        "id": note_id,
        "course_id": note.course_id,
        "course_code": course["code"],
        "course_title": course["title"],
        "title": note.title.strip(),
        "topic": note.topic.strip(),
        "content": note.content.strip(),
        "tags": note.tags or "",
        "is_favorite": False,
        "created_at": str(created_at)
    })


@app.post("/api/notes/upload-pdf", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def upload_pdf_note(
    course_id: int = Form(...),
    title: str = Form(...),
    topic: str = Form(...),
    file: UploadFile = File(...)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files (.pdf) are supported")

    content_bytes = await file.read()
    parsed = extract_text_from_pdf_bytes(content_bytes)

    conn = get_db_connection()
    course = conn.execute("SELECT code, title FROM courses WHERE id = ?;", (course_id,)).fetchone()
    if not course:
        conn.close()
        raise HTTPException(status_code=404, detail="Course not found")

    cursor = conn.execute(
        "INSERT INTO notes (course_id, title, topic, content) VALUES (?, ?, ?, ?) RETURNING id, created_at;",
        (course_id, title.strip(), topic.strip(), parsed["content"])
    )
    row = cursor.fetchone()
    conn.commit()
    note_id, created_at = row["id"], row["created_at"]
    conn.close()

    return {
        "id": note_id,
        "course_id": course_id,
        "course_code": course["code"],
        "course_title": course["title"],
        "title": title.strip(),
        "topic": topic.strip(),
        "content": parsed["content"],
        "created_at": str(created_at)
    }


@app.put("/api/notes/{note_id}", response_model=NoteResponse)
def update_note(note_id: int, note_update: NoteUpdate):
    """Updates an existing note's title, topic, content, tags, or favorite status."""
    conn = get_db_connection()
    existing = conn.execute("SELECT * FROM notes WHERE id = ?;", (note_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Note not found")

    new_title = note_update.title.strip() if note_update.title is not None else existing["title"]
    new_topic = note_update.topic.strip() if note_update.topic is not None else existing["topic"]
    new_content = note_update.content.strip() if note_update.content is not None else existing["content"]
    new_tags = note_update.tags.strip() if note_update.tags is not None else (existing["tags"] or "")
    new_fav = int(note_update.is_favorite) if note_update.is_favorite is not None else (existing["is_favorite"] or 0)

    # Record history snapshot before applying edits
    conn.execute("""
    INSERT INTO note_history (note_id, title, topic, content, tags, change_summary)
    VALUES (?, ?, ?, ?, ?, ?);
    """, (
        existing["id"],
        existing["title"],
        existing["topic"],
        existing["content"],
        existing["tags"] or "",
        "Updated note fields"
    ))

    # Invalidate cached quiz & flashcards if content changed
    if note_update.content is not None and note_update.content.strip() != existing["content"]:
        conn.execute("DELETE FROM quizzes WHERE note_id = ?;", (note_id,))
        conn.execute("DELETE FROM flashcards WHERE note_id = ?;", (note_id,))

    conn.execute("""
    UPDATE notes
    SET title = ?, topic = ?, content = ?, tags = ?, is_favorite = ?
    WHERE id = ?;
    """, (new_title, new_topic, new_content, new_tags, new_fav, note_id))
    conn.commit()

    updated = conn.execute("""
    SELECT n.*, c.code as course_code, c.title as course_title
    FROM notes n
    JOIN courses c ON n.course_id = c.id
    WHERE n.id = ?;
    """, (note_id,)).fetchone()
    conn.close()

    return enrich_note_dict(dict(updated))


@app.get("/api/notes/{note_id}/history", response_model=List[NoteHistoryResponse], tags=["Notes"])
def get_note_history(note_id: int):
    """Retrieves revision history snapshots for a given note."""
    conn = get_db_connection()
    note = conn.execute("SELECT id FROM notes WHERE id = ?;", (note_id,)).fetchone()
    if not note:
        conn.close()
        raise HTTPException(status_code=404, detail="Note not found")

    rows = conn.execute("""
        SELECT id, note_id, title, topic, content, tags, change_summary, created_at
        FROM note_history
        WHERE note_id = ?
        ORDER BY id DESC;
    """, (note_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/api/notes/{note_id}/revert/{history_id}", response_model=NoteResponse, tags=["Notes"])
def revert_note_to_history(note_id: int, history_id: int):
    """Reverts a note to an earlier revision snapshot recorded in note_history."""
    conn = get_db_connection()
    note = conn.execute("SELECT * FROM notes WHERE id = ?;", (note_id,)).fetchone()
    if not note:
        conn.close()
        raise HTTPException(status_code=404, detail="Note not found")

    history = conn.execute("""
        SELECT * FROM note_history WHERE id = ? AND note_id = ?;
    """, (history_id, note_id)).fetchone()
    if not history:
        conn.close()
        raise HTTPException(status_code=404, detail="History revision not found")

    # Record current state to history before rollback
    conn.execute("""
        INSERT INTO note_history (note_id, title, topic, content, tags, change_summary)
        VALUES (?, ?, ?, ?, ?, ?);
    """, (
        note["id"],
        note["title"],
        note["topic"],
        note["content"],
        note["tags"] or "",
        f"Pre-revert snapshot before reverting to history #{history_id}"
    ))

    # Apply historical state
    conn.execute("""
        UPDATE notes
        SET title = ?, topic = ?, content = ?, tags = ?
        WHERE id = ?;
    """, (history["title"], history["topic"], history["content"], history["tags"], note_id))

    # Invalidate cache
    conn.execute("DELETE FROM quizzes WHERE note_id = ?;", (note_id,))
    conn.execute("DELETE FROM flashcards WHERE note_id = ?;", (note_id,))
    conn.commit()

    reverted = conn.execute("""
        SELECT n.*, c.code as course_code, c.title as course_title
        FROM notes n
        JOIN courses c ON n.course_id = c.id
        WHERE n.id = ?;
    """, (note_id,)).fetchone()
    conn.close()

    return enrich_note_dict(dict(reverted))


@app.post("/api/notes/{note_id}/favorite", response_model=FavoriteToggleResponse)
def toggle_note_favorite(note_id: int):
    """Toggles bookmark/favorite status for a study note."""
    conn = get_db_connection()
    note = conn.execute("SELECT id, is_favorite FROM notes WHERE id = ?;", (note_id,)).fetchone()
    if not note:
        conn.close()
        raise HTTPException(status_code=404, detail="Note not found")

    new_status = 0 if note["is_favorite"] else 1
    conn.execute("UPDATE notes SET is_favorite = ? WHERE id = ?;", (new_status, note_id))
    conn.commit()
    conn.close()

    return {
        "id": note_id,
        "is_favorite": bool(new_status),
        "message": "Note added to favorites" if new_status else "Note removed from favorites"
    }


@app.post("/api/notes/{note_id}/pin")
def toggle_note_pin(note_id: int):
    """Toggles pinned/sticky status for a study note."""
    conn = get_db_connection()
    note = conn.execute("SELECT id, is_pinned FROM notes WHERE id = ?;", (note_id,)).fetchone()
    if not note:
        conn.close()
        raise HTTPException(status_code=404, detail="Note not found")
    new_status = 0 if note["is_pinned"] else 1
    conn.execute("UPDATE notes SET is_pinned = ? WHERE id = ?;", (new_status, note_id))
    conn.commit()
    conn.close()
    return {"id": note_id, "is_pinned": bool(new_status)}


@app.get("/api/notes/{note_id}/export/markdown")
def export_note_markdown(note_id: int):
    """Exports note as formatted Markdown file."""
    conn = get_db_connection()
    note = conn.execute("""
    SELECT n.*, c.code as course_code, c.title as course_title
    FROM notes n
    JOIN courses c ON n.course_id = c.id
    WHERE n.id = ?;
    """, (note_id,)).fetchone()
    conn.close()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    safe_title = "".join(c for c in note["title"] if c.isalnum() or c in (" ", "-", "_")).strip().replace(" ", "_")
    filename = f"{note['course_code']}_{safe_title}.md"

    md_content = f"""# {note['title']}

**Course:** {note['course_code']} - {note['course_title']}  
**Topic:** {note['topic']}  
**Tags:** {note['tags'] or 'None'}  
**Created At:** {note['created_at']}  

---

## Content

{note['content']}
"""
    return Response(
        content=md_content,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@app.get("/api/notes/{note_id}/export/json")
def export_note_json(note_id: int):
    """Exports note along with course info, cached quiz, and flashcards as JSON."""
    conn = get_db_connection()
    note = conn.execute("""
    SELECT n.*, c.code as course_code, c.title as course_title, c.department
    FROM notes n
    JOIN courses c ON n.course_id = c.id
    WHERE n.id = ?;
    """, (note_id,)).fetchone()
    if not note:
        conn.close()
        raise HTTPException(status_code=404, detail="Note not found")

    cached_quiz = conn.execute("SELECT questions_json FROM quizzes WHERE note_id = ?;", (note_id,)).fetchone()
    cached_cards = conn.execute("SELECT cards_json FROM flashcards WHERE note_id = ?;", (note_id,)).fetchone()
    conn.close()

    export_payload = {
        "id": note["id"],
        "title": note["title"],
        "topic": note["topic"],
        "tags": [t.strip() for t in note["tags"].split(",") if t.strip()] if note["tags"] else [],
        "content": note["content"],
        "is_favorite": bool(note["is_favorite"]),
        "created_at": str(note["created_at"]),
        "course": {
            "code": note["course_code"],
            "title": note["course_title"],
            "department": note["department"]
        },
        "quiz": json.loads(cached_quiz["questions_json"]) if cached_quiz else None,
        "flashcards": json.loads(cached_cards["cards_json"]) if cached_cards else None
    }

    safe_title = "".join(c for c in note["title"] if c.isalnum() or c in (" ", "-", "_")).strip().replace(" ", "_")
    filename = f"{note['course_code']}_{safe_title}.json"

    return Response(
        content=json.dumps(export_payload, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@app.get("/api/notes/{note_id}/export/txt")
def export_note_txt(note_id: int):
    """Exports note as stripped plain text without markdown syntax."""
    conn = get_db_connection()
    note = conn.execute("""
    SELECT n.*, c.code as course_code, c.title as course_title
    FROM notes n
    JOIN courses c ON n.course_id = c.id
    WHERE n.id = ?;
    """, (note_id,)).fetchone()
    conn.close()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    clean_content = strip_markdown_formatting(note["content"])
    txt = f"TITLE: {note['title']}\nCOURSE: {note['course_code']} - {note['course_title']}\nTOPIC: {note['topic']}\n\nCONTENT:\n{clean_content}\n"

    safe_title = "".join(c for c in note["title"] if c.isalnum() or c in (" ", "-", "_")).strip().replace(" ", "_")
    filename = f"{note['course_code']}_{safe_title}.txt"

    return Response(
        content=txt,
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@app.get("/api/notes/{note_id}/export/anki")
def export_note_anki(note_id: int):
    """Exports note flashcards in Anki-compatible TSV format."""
    conn = get_db_connection()
    note = conn.execute("""
    SELECT n.*, c.code as course_code
    FROM notes n
    JOIN courses c ON n.course_id = c.id
    WHERE n.id = ?;
    """, (note_id,)).fetchone()
    if not note:
        conn.close()
        raise HTTPException(status_code=404, detail="Note not found")

    cached = conn.execute("SELECT cards_json FROM flashcards WHERE note_id = ?;", (note_id,)).fetchone()
    if cached:
        cards = json.loads(cached["cards_json"])
    else:
        cards = generate_flashcards_from_notes(note["title"], note["content"])
        conn.execute(
            "INSERT OR REPLACE INTO flashcards (note_id, cards_json) VALUES (?, ?);",
            (note_id, json.dumps(cards))
        )
        conn.commit()
    conn.close()

    deck_name = f"{note['course_code']}::{note['topic'].replace(' ', '_')}"
    tsv_content = serialize_cards_to_anki(cards, deck_name=deck_name)
    safe_title = "".join(c for c in note["title"] if c.isalnum() or c in (" ", "-", "_")).strip().replace(" ", "_")
    filename = f"{note['course_code']}_{safe_title}_anki.tsv"

    return Response(
        content=tsv_content,
        media_type="text/tab-separated-values",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@app.delete("/api/notes/bulk", response_model=BulkDeleteResponse)
def delete_notes_bulk(req: BulkDeleteRequest):
    """Deletes multiple notes in a single batch transaction."""
    if not req.note_ids:
        return {"deleted_count": 0, "deleted_ids": []}
    conn = get_db_connection()
    placeholders = ",".join("?" for _ in req.note_ids)
    cursor = conn.execute(f"DELETE FROM notes WHERE id IN ({placeholders});", req.note_ids)
    conn.commit()
    count = cursor.rowcount
    conn.close()
    return {"deleted_count": count, "deleted_ids": req.note_ids}


@app.delete("/api/notes/{note_id}")
def delete_note(note_id: int):
    conn = get_db_connection()
    cursor = conn.execute("DELETE FROM notes WHERE id = ?;", (note_id,))
    conn.commit()
    conn.close()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"message": "Note deleted successfully"}


@app.get("/api/notes/{note_id}/summary")
def get_note_summary(note_id: int):
    """Generates concise executive bullet summaries from note contents."""
    conn = get_db_connection()
    note = conn.execute("SELECT id, title, content FROM notes WHERE id = ?;", (note_id,)).fetchone()
    conn.close()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    bullets = extract_bullet_summary(note["content"])
    return {
        "note_id": note_id,
        "title": note["title"],
        "bullet_count": len(bullets),
        "summary_bullets": bullets
    }


@app.get("/api/notes/{note_id}/concepts")
def get_note_concepts(note_id: int):
    """Extracts key concepts and terms from a note using NLP frequency analysis."""
    conn = get_db_connection()
    note = conn.execute("SELECT id, title, content FROM notes WHERE id = ?;", (note_id,)).fetchone()
    conn.close()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    concepts = extract_key_concepts(f"{note['title']} \n {note['content']}")
    return {"note_id": note_id, "title": note["title"], "concepts": concepts}


@app.get("/api/notes/{note_id}/takeaways", tags=["Notes"])
def get_note_takeaways(note_id: int):
    """Extracts explicit definitions and bulleted key takeaways from study notes."""
    conn = get_db_connection()
    note = conn.execute("SELECT id, title, topic, content FROM notes WHERE id = ?;", (note_id,)).fetchone()
    conn.close()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    extracted = extract_definitions_and_takeaways(note["content"])
    return {
        "note_id": note_id,
        "title": note["title"],
        "topic": note["topic"],
        "definition_count": len(extracted["definitions"]),
        "takeaway_count": len(extracted["takeaways"]),
        "definitions": extracted["definitions"],
        "takeaways": extracted["takeaways"]
    }


@app.get("/api/notes/{note_id}/code-snippets", tags=["Notes"])
def get_note_code_snippets(note_id: int):
    """Extracts programming code snippets and language syntax stats from a study note."""
    conn = get_db_connection()
    note = conn.execute("SELECT id, title, content FROM notes WHERE id = ?;", (note_id,)).fetchone()
    conn.close()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    result = extract_code_snippets(note["content"])
    result["note_id"] = note_id
    result["title"] = note["title"]
    return result


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


@app.post("/api/notes/{note_id}/quiz/regenerate", response_model=QuizGenerateResponse)
def regenerate_quiz(note_id: int):
    """Bypasses cache and generates a fresh quiz for the given note."""
    conn = get_db_connection()
    note = conn.execute("SELECT id, title, content FROM notes WHERE id = ?;", (note_id,)).fetchone()
    if not note:
        conn.close()
        raise HTTPException(status_code=404, detail="Note not found")

    conn.execute("DELETE FROM quizzes WHERE note_id = ?;", (note_id,))
    questions = generate_quiz_from_notes(note["title"], note["content"])
    conn.execute(
        "INSERT INTO quizzes (note_id, questions_json) VALUES (?, ?);",
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


@app.post("/api/notes/{note_id}/import/flashcards", response_model=FlashcardImportResponse, tags=["Flashcards"])
def import_note_flashcards(note_id: int, req: FlashcardImportRequest):
    """Imports external flashcards into a study note's deck."""
    conn = get_db_connection()
    note = conn.execute("SELECT id, topic FROM notes WHERE id = ?;", (note_id,)).fetchone()
    if not note:
        conn.close()
        raise HTTPException(status_code=404, detail="Note not found")

    cached = conn.execute("SELECT cards_json FROM flashcards WHERE note_id = ?;", (note_id,)).fetchone()
    existing_cards = json.loads(cached["cards_json"]) if cached else []

    if req.replace_existing:
        target_cards = []
        next_id = 1
    else:
        target_cards = existing_cards
        next_id = max([c.get("id", 0) for c in target_cards], default=0) + 1

    imported_count = 0
    for item in req.cards:
        if not item.front.strip() or not item.back.strip():
            continue
        target_cards.append({
            "id": next_id,
            "front": item.front.strip(),
            "back": item.back.strip(),
            "topic": item.topic.strip() if item.topic else note["topic"]
        })
        next_id += 1
        imported_count += 1

    conn.execute(
        "INSERT OR REPLACE INTO flashcards (note_id, cards_json) VALUES (?, ?);",
        (note_id, json.dumps(target_cards))
    )
    conn.commit()
    conn.close()

    return {
        "note_id": note_id,
        "imported_count": imported_count,
        "total_cards": len(target_cards),
        "message": f"Successfully imported {imported_count} flashcards"
    }


@app.post("/api/notes/{note_id}/cloze-cards")
def get_cloze_flashcards(note_id: int):
    """Generates fill-in-the-blank (Cloze Deletion) flashcards from note concepts."""
    conn = get_db_connection()
    note = conn.execute("SELECT id, title, content FROM notes WHERE id = ?;", (note_id,)).fetchone()
    conn.close()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    cards = generate_cloze_flashcards(note["title"], note["content"])
    return {"note_id": note_id, "note_title": note["title"], "cloze_cards": cards}


@app.post("/api/flashcards/review")
def review_flashcard_sm2(
    rating: int,
    repetitions: int = 0,
    ease_factor: float = 2.5,
    interval_days: int = 1
):
    """Calculates next review schedule using the SuperMemo-2 (SM-2) algorithm."""
    if not (1 <= rating <= 4):
        raise HTTPException(status_code=400, detail="Rating must be between 1 (Again) and 4 (Easy)")
    res = calculate_sm2(rating, repetitions, ease_factor, interval_days)
    res["retention_forecast"] = estimate_retention_probability(res["interval_days"], 0, res["ease_factor"])
    res["urgency"] = classify_card_urgency(0)
    return res


@app.get("/api/flashcards/due")
def get_due_flashcard_decks():
    """Returns all note decks currently cached and available for active recall practice."""
    conn = get_db_connection()
    rows = conn.execute("""
    SELECT f.note_id, f.created_at, n.title as note_title, c.code as course_code, f.cards_json
    FROM flashcards f
    JOIN notes n ON f.note_id = n.id
    JOIN courses c ON n.course_id = c.id
    ORDER BY f.created_at DESC;
    """).fetchall()
    conn.close()

    decks = []
    for r in rows:
        try:
            cards = json.loads(r["cards_json"])
            card_count = len(cards)
        except Exception:
            card_count = 0
        decks.append({
            "note_id": r["note_id"],
            "note_title": r["note_title"],
            "course_code": r["course_code"],
            "card_count": card_count,
            "created_at": str(r["created_at"])
        })
    return {"total_decks": len(decks), "decks": decks}


@app.get("/api/flashcards/decay-forecast", tags=["Flashcards"])
def get_retention_decay_forecast(
    interval_days: int = 6,
    ease_factor: float = 2.5,
    days_ahead: int = 14
):
    """Generates day-by-day projected memory retention curve using Ebbinghaus decay model."""
    if interval_days < 1:
        raise HTTPException(status_code=400, detail="interval_days must be >= 1")
    if ease_factor < 1.0:
        raise HTTPException(status_code=400, detail="ease_factor must be >= 1.0")

    forecast = project_retention_curve(interval_days, ease_factor, days_ahead)
    sub_80 = next((p["day"] for p in forecast if p["retention_percent"] < 80.0), None)

    return {
        "interval_days": interval_days,
        "ease_factor": ease_factor,
        "recommended_review_day": sub_80 if sub_80 is not None else days_ahead,
        "projection": forecast
    }


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


@app.get("/api/quiz-attempts/{attempt_id}")
def get_quiz_attempt_detail(attempt_id: int):
    """Retrieves full metadata and score results for a specific quiz attempt."""
    conn = get_db_connection()
    row = conn.execute("""
    SELECT qa.*, n.title as note_title, c.code as course_code, c.title as course_title
    FROM quiz_attempts qa
    JOIN notes n ON qa.note_id = n.id
    JOIN courses c ON n.course_id = c.id
    WHERE qa.id = ?;
    """, (attempt_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Quiz attempt not found")

    pct = round((row["score"] / max(1, row["total_questions"])) * 100, 1)
    return {
        "id": row["id"],
        "note_id": row["note_id"],
        "note_title": row["note_title"],
        "course_code": row["course_code"],
        "course_title": row["course_title"],
        "score": row["score"],
        "total_questions": row["total_questions"],
        "time_taken_seconds": row["time_taken_seconds"],
        "percentage": pct,
        "created_at": str(row["created_at"])
    }


@app.get("/api/tags", response_model=List[TagCount])
def get_all_tags():
    """Aggregates all unique note tags and their occurrence frequencies."""
    conn = get_db_connection()
    rows = conn.execute("SELECT tags FROM notes WHERE tags != '';").fetchall()
    conn.close()
    counts = {}
    for r in rows:
        for t in r["tags"].split(","):
            cleaned = t.strip().lower()
            if cleaned:
                counts[cleaned] = counts.get(cleaned, 0) + 1
    return [{"tag": k, "count": v} for k, v in sorted(counts.items(), key=lambda x: x[1], reverse=True)]


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


@app.post("/api/study-sessions", status_code=status.HTTP_201_CREATED)
def log_study_session(session: StudySessionCreate):
    """Logs dedicated focus minutes spent studying a course."""
    conn = get_db_connection()
    cursor = conn.execute(
        "INSERT INTO study_sessions (course_id, duration_minutes, session_type) VALUES (?, ?, ?) RETURNING id, created_at;",
        (session.course_id, session.duration_minutes, session.session_type)
    )
    row = cursor.fetchone()
    conn.commit()
    conn.close()
    return {"id": row["id"], "course_id": session.course_id, "duration_minutes": session.duration_minutes, "session_type": session.session_type}


@app.get("/api/study-sessions/stats", response_model=StudySessionSummary, tags=["Analytics"])
def get_study_session_stats():
    """Returns aggregated focus time, breakdown by session activity, and distribution per course."""
    conn = get_db_connection()
    total_row = conn.execute("""
        SELECT COALESCE(SUM(duration_minutes), 0) as total_mins, COUNT(id) as total_sessions
        FROM study_sessions;
    """).fetchone()

    type_rows = conn.execute("""
        SELECT session_type, COALESCE(SUM(duration_minutes), 0) as mins
        FROM study_sessions
        GROUP BY session_type;
    """).fetchall()
    by_type = {r["session_type"]: r["mins"] for r in type_rows}

    course_rows = conn.execute("""
        SELECT s.course_id, c.code as course_code, c.title as course_title,
               COALESCE(SUM(s.duration_minutes), 0) as total_minutes,
               COUNT(s.id) as session_count
        FROM study_sessions s
        JOIN courses c ON s.course_id = c.id
        GROUP BY s.course_id
        ORDER BY total_minutes DESC;
    """).fetchall()
    conn.close()

    by_course = [
        CourseFocusStats(
            course_id=r["course_id"],
            course_code=r["course_code"],
            course_title=r["course_title"],
            total_minutes=r["total_minutes"],
            session_count=r["session_count"]
        )
        for r in course_rows
    ]

    return {
        "total_focus_minutes": total_row["total_mins"],
        "total_sessions": total_row["total_sessions"],
        "by_session_type": by_type,
        "by_course": by_course
    }


@app.get("/api/analytics/activity")
def get_study_activity():
    """Returns study activity timeline, score trends, and streak."""
    conn = get_db_connection()
    recent_attempts = conn.execute("""
    SELECT qa.id, qa.score, qa.total_questions, qa.time_taken_seconds, qa.created_at,
           n.title as note_title, c.code as course_code
    FROM quiz_attempts qa
    JOIN notes n ON qa.note_id = n.id
    JOIN courses c ON n.course_id = c.id
    ORDER BY qa.created_at DESC
    LIMIT 10;
    """).fetchall()

    daily_counts = conn.execute("""
    SELECT DATE(created_at) as date, COUNT(*) as count, AVG(CAST(score AS FLOAT) / total_questions * 100) as avg_pct
    FROM quiz_attempts
    GROUP BY DATE(created_at)
    ORDER BY date DESC
    LIMIT 7;
    """).fetchall()
    conn.close()

    history = [
        {
            "id": r["id"],
            "score": r["score"],
            "total": r["total_questions"],
            "percentage": round((r["score"] / max(1, r["total_questions"])) * 100, 1),
            "note_title": r["note_title"],
            "course_code": r["course_code"],
            "date": str(r["created_at"])
        }
        for r in recent_attempts
    ]

    daily = [
        {
            "date": r["date"],
            "count": r["count"],
            "avg_score": round(r["avg_pct"] or 0, 1)
        }
        for r in daily_counts
    ]

    # Calculate streak (minimum 1 if at least one attempt exists)
    streak = 1 if history else 0

    return {
        "recent_attempts": history,
        "daily_breakdown": daily,
        "current_streak_days": streak
    }


@app.get("/api/analytics/badges", tags=["Analytics"])
def get_user_badges():
    """Calculates student milestones, achievement badges, and current unlocked statuses."""
    conn = get_db_connection()
    c_count = conn.execute("SELECT COUNT(*) FROM courses;").fetchone()[0]
    n_count = conn.execute("SELECT COUNT(*) FROM notes;").fetchone()[0]
    q_stats = conn.execute("""
        SELECT COUNT(id) as count, AVG(CAST(score AS FLOAT) / total_questions * 100) as avg_score
        FROM quiz_attempts;
    """).fetchone()
    f_mins = conn.execute("SELECT COALESCE(SUM(duration_minutes), 0) FROM study_sessions;").fetchone()[0]
    conn.close()

    metrics = {
        "total_courses": c_count,
        "total_notes": n_count,
        "quizzes_taken": q_stats["count"] or 0,
        "average_score_percent": round(q_stats["avg_score"] or 0.0, 1),
        "total_focus_minutes": f_mins
    }

    badges = evaluate_badges(metrics)
    unlocked_count = sum(1 for b in badges if b["unlocked"])

    return {
        "unlocked_count": unlocked_count,
        "total_badges": len(badges),
        "badges": badges
    }
