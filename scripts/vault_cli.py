#!/usr/bin/env python3
"""
StudyVault Command-Line Interface (CLI) Management Utility.
Allows terminal-based navigation of courses, notes, and system maintenance.
"""

import argparse
import os
import sys
from pathlib import Path

# Ensure src/ is on Python module search path
BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
sys.path.insert(0, str(SRC_DIR))

from database import get_db_connection


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="studyvault",
        description="StudyVault Course Notes & AI Quiz Hub CLI Tool",
        epilog="Use 'studyvault <command> --help' for details on a specific command."
    )
    parser.add_argument("--version", action="version", version="StudyVault CLI v1.5.0")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: status
    subparsers.add_parser("status", help="Check database connectivity and general vault health")

    # Command: courses
    p_courses = subparsers.add_parser("courses", help="List enrolled courses or inspect course details")
    p_courses.add_argument("--archived", action="store_true", help="Include archived courses")
    p_courses.add_argument("--code", type=str, help="Show details for specific course code (e.g. CS101)")

    # Command: notes
    p_notes = subparsers.add_parser("notes", help="List and search study notes in the vault")
    p_notes.add_argument("--course", type=str, help="Filter by course code")
    p_notes.add_argument("--search", type=str, help="Search by keyword in title or topic")
    p_notes.add_argument("--favorites", action="store_true", help="Filter bookmarked/favorite notes")

    return parser


def handle_courses(args) -> int:
    conn = get_db_connection()
    if args.code:
        course = conn.execute("SELECT * FROM courses WHERE code = ?;", (args.code.upper(),)).fetchone()
        if not course:
            print(f"❌ Course '{args.code}' not found.", file=sys.stderr)
            conn.close()
            return 1
        note_count = conn.execute("SELECT COUNT(*) FROM notes WHERE course_id = ?;", (course["id"],)).fetchone()[0]
        print(f"\n📚 {course['code']} - {course['title']}")
        print(f"   Department : {course['department']}")
        print(f"   Instructor : {course['instructor'] or 'Unassigned'}")
        print(f"   Term       : {course['term']}")
        print(f"   Notes      : {note_count}")
        print(f"   Archived   : {'Yes' if course['is_archived'] else 'No'}\n")
        conn.close()
        return 0

    where = "" if args.archived else "WHERE is_archived = 0"
    rows = conn.execute(f"""
        SELECT c.code, c.title, c.department, c.is_archived, COUNT(n.id) as notes
        FROM courses c
        LEFT JOIN notes n ON c.id = n.course_id
        {where}
        GROUP BY c.id
        ORDER BY c.code ASC;
    """).fetchall()
    conn.close()

    print(f"\n{'CODE':<10} {'TITLE':<38} {'DEPT':<22} {'NOTES':<6} {'ARCHIVED'}")
    print("-" * 85)
    for r in rows:
        arch_str = "[ARCHIVED]" if r["is_archived"] else ""
        print(f"{r['code']:<10} {r['title'][:36]:<38} {r['department'][:20]:<22} {r['notes']:<6} {arch_str}")
    print()
    return 0


def handle_notes(args) -> int:
    conn = get_db_connection()
    query = """
        SELECT n.id, n.title, n.topic, n.is_favorite, n.is_pinned, c.code as course_code
        FROM notes n
        JOIN courses c ON n.course_id = c.id
        WHERE 1=1
    """
    params = []
    if args.course:
        query += " AND c.code = ?"
        params.append(args.course.upper())
    if args.favorites:
        query += " AND n.is_favorite = 1"
    if args.search:
        query += " AND (n.title LIKE ? OR n.topic LIKE ? OR n.content LIKE ?)"
        term = f"%{args.search}%"
        params.extend([term, term, term])

    query += " ORDER BY n.is_pinned DESC, n.id DESC;"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    if not rows:
        print("No matching notes found.")
        return 0

    print(f"\n{'ID':<5} {'COURSE':<10} {'TOPIC':<25} {'TITLE':<40} {'FLAGS'}")
    print("-" * 85)
    for r in rows:
        flags = []
        if r["is_pinned"]:
            flags.append("PINNED")
        if r["is_favorite"]:
            flags.append("★")
        flag_str = " ".join(flags)
        print(f"{r['id']:<5} {r['course_code']:<10} {r['topic'][:23]:<25} {r['title'][:38]:<40} {flag_str}")
    print()
    return 0




def handle_status() -> int:
    try:
        conn = get_db_connection()
        conn.execute("SELECT 1;").fetchone()
        conn.close()
        print("✅ StudyVault database connection is healthy.")
        return 0
    except Exception as e:
        print(f"❌ Database error: {e}", file=sys.stderr)
        return 1


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "status":
        return handle_status()
    elif args.command == "courses":
        return handle_courses(args)
    elif args.command == "notes":
        return handle_notes(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
