"""
Unit tests for database integrity, foreign keys, and cascading deletion.
"""

import os
import sys
import sqlite3
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from database import get_db_connection, get_db_ctx, init_db


def test_init_db_and_courses_exist():
    init_db()
    with get_db_ctx() as conn:
        count = conn.execute("SELECT COUNT(*) FROM courses;").fetchone()[0]
        assert count >= 3


def test_foreign_key_enforcement():
    with pytest.raises(sqlite3.IntegrityError):
        with get_db_ctx() as conn:
            conn.execute(
                "INSERT INTO notes (course_id, title, topic, content) VALUES (999999, 'Orphan Note', 'None', 'Content');"
            )


def test_cascade_delete_course_removes_notes():
    with get_db_ctx() as conn:
        # Create temporary course
        c = conn.execute("INSERT INTO courses (code, title, department) VALUES ('TMP999', 'Temp Course', 'Temp') RETURNING id;").fetchone()
        course_id = c["id"]

        # Create note under course
        n = conn.execute(
            "INSERT INTO notes (course_id, title, topic, content) VALUES (?, 'Temp Note', 'Temp', 'Content') RETURNING id;",
            (course_id,)
        ).fetchone()
        note_id = n["id"]

    # Delete course
    with get_db_ctx() as conn:
        conn.execute("DELETE FROM courses WHERE id = ?;", (course_id,))

    # Verify note was cascaded
    with get_db_ctx() as conn:
        check = conn.execute("SELECT COUNT(*) FROM notes WHERE id = ?;", (note_id,)).fetchone()[0]
        assert check == 0
