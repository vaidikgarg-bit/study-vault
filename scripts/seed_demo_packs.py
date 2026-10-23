#!/usr/bin/env python3
"""
StudyVault Demo Study Pack Seeder.
Imports curated curriculum packs into the SQLite database.
"""

import json
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
DATA_FILE = BASE_DIR / "data" / "study_packs.json"
sys.path.insert(0, str(SRC_DIR))

from database import get_db_connection


def seed_packs(json_path=DATA_FILE) -> int:
    if not os.path.exists(json_path):
        print(f"❌ Seed data file not found at {json_path}", file=sys.stderr)
        return 1

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    conn = get_db_connection()
    inserted_courses = 0
    inserted_notes = 0

    try:
        with conn:
            for item in data.get("packs", []):
                c = item["course"]
                cursor = conn.execute(
                    "INSERT OR IGNORE INTO courses (code, title, department, color, instructor, term) VALUES (?, ?, ?, ?, ?, ?);",
                    (c["code"], c["title"], c["department"], c.get("color", "indigo"), c.get("instructor", ""), c.get("term", "Fall 2026"))
                )
                if cursor.rowcount > 0:
                    inserted_courses += 1

                course_id = conn.execute("SELECT id FROM courses WHERE code = ?;", (c["code"],)).fetchone()[0]

                for n in item.get("notes", []):
                    # Check if note title exists
                    exists = conn.execute("SELECT id FROM notes WHERE course_id = ? AND title = ?;", (course_id, n["title"])).fetchone()
                    if not exists:
                        conn.execute(
                            "INSERT INTO notes (course_id, title, topic, content, tags) VALUES (?, ?, ?, ?, ?);",
                            (course_id, n["title"], n["topic"], n["content"], n.get("tags", ""))
                        )
                        inserted_notes += 1
    finally:
        conn.close()

    print(f"✅ Seeding complete: {inserted_courses} courses, {inserted_notes} study notes added.")
    return 0


if __name__ == "__main__":
    sys.exit(seed_packs())
