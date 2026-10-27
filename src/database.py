"""
SQLite Database Layer and seed data initialization for StudyVault.
"""

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime

from config import DB_PATH


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def get_db_ctx():
    """Context manager for SQLite connections ensuring clean auto-commit and closure."""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Courses Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL UNIQUE,
        title TEXT NOT NULL,
        department TEXT NOT NULL,
        color TEXT DEFAULT 'indigo',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Notes Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        topic TEXT NOT NULL,
        content TEXT NOT NULL,
        is_favorite INTEGER DEFAULT 0,
        tags TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
    );
    """)

    # Ensure schema migrations for existing databases
    cursor.execute("PRAGMA table_info(notes);")
    columns = [col[1] for col in cursor.fetchall()]
    if "is_favorite" not in columns:
        cursor.execute("ALTER TABLE notes ADD COLUMN is_favorite INTEGER DEFAULT 0;")
    if "tags" not in columns:
        cursor.execute("ALTER TABLE notes ADD COLUMN tags TEXT DEFAULT '';")
    if "is_pinned" not in columns:
        cursor.execute("ALTER TABLE notes ADD COLUMN is_pinned INTEGER DEFAULT 0;")
    cursor.execute("PRAGMA table_info(courses);")
    c_cols = [c[1] for c in cursor.fetchall()]
    if "instructor" not in c_cols:
        cursor.execute("ALTER TABLE courses ADD COLUMN instructor TEXT DEFAULT '';")
    if "term" not in c_cols:
        cursor.execute("ALTER TABLE courses ADD COLUMN term TEXT DEFAULT 'Fall 2026';")

    # Cached Quizzes Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quizzes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        note_id INTEGER NOT NULL UNIQUE,
        questions_json TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (note_id) REFERENCES notes (id) ON DELETE CASCADE
    );
    """)

    # Cached Flashcards Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS flashcards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        note_id INTEGER NOT NULL UNIQUE,
        cards_json TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (note_id) REFERENCES notes (id) ON DELETE CASCADE
    );
    """)

    # Quiz Attempts & Performance Analytics
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quiz_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        note_id INTEGER NOT NULL,
        score INTEGER NOT NULL,
        total_questions INTEGER NOT NULL,
        time_taken_seconds INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (note_id) REFERENCES notes (id) ON DELETE CASCADE
    );
    """)

    # Study Sessions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS study_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER NOT NULL,
        duration_minutes INTEGER NOT NULL,
        session_type TEXT DEFAULT 'reading',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
    );
    """)

    # Note History / Versioning Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS note_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        note_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        topic TEXT NOT NULL,
        content TEXT NOT NULL,
        tags TEXT DEFAULT '',
        change_summary TEXT DEFAULT 'Update note content',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (note_id) REFERENCES notes (id) ON DELETE CASCADE
    );
    """)

    # Performance Indices
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_course_id ON notes(course_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_favorite ON notes(is_favorite);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_pinned ON notes(is_pinned);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_courses_code ON courses(code);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_note_history_note_id ON note_history(note_id);")

    # Check if we should seed default student courses
    cursor.execute("SELECT COUNT(*) FROM courses;")
    if cursor.fetchone()[0] == 0:
        _seed_default_data(cursor)

    conn.commit()
    conn.close()


def _seed_default_data(cursor):
    courses = [
        ("CS101", "Data Structures & Algorithms", "Computer Science", "indigo"),
        ("MATH200", "Discrete Mathematics & Logic", "Mathematics", "emerald"),
        ("EE102", "Digital Systems & Computer Architecture", "Electrical Engineering", "amber")
    ]
    cursor.executemany("INSERT INTO courses (code, title, department, color) VALUES (?, ?, ?, ?);", courses)

    notes = [
        (
            1,
            "Binary Search Trees & Traversal Algorithms",
            "Trees & Hierarchies",
            """A Binary Search Tree (BST) is a hierarchical node-based data structure where each node has at most two children.
Key Invariant:
For any given node N:
1. Every key in N's left subtree is strictly less than N.key.
2. Every key in N's right subtree is strictly greater than N.key.

Time Complexities:
- Search: O(log N) average, O(N) worst case (skewed / unbalanced tree).
- Insertion: O(log N) average, O(N) worst case.
- Deletion: O(log N) average, O(N) worst case.

Tree Traversal Techniques:
1. In-Order (Left, Root, Right): Visits nodes in non-decreasing sorted order.
2. Pre-Order (Root, Left, Right): Useful for cloning or serializing a tree structure.
3. Post-Order (Left, Right, Root): Useful for deleting trees or calculating bottom-up attributes (like height).
4. Level-Order (Breadth-First): Traverses level by level using a Queue (FIFO).

Self-Balancing Trees:
To prevent worst-case O(N) degeneration, self-balancing BSTs like AVL trees and Red-Black trees perform tree rotations to guarantee O(log N) height."""
        ),
        (
            1,
            "Graph Representations & Dijkstra's Algorithm",
            "Graph Theory",
            """Graphs G = (V, E) consist of a set of vertices V and edges E.
Representations:
1. Adjacency Matrix: V x V 2D array. Fast edge lookup O(1), but consumes O(V^2) space.
2. Adjacency List: Array or hash map of lists. Space efficient O(V + E), optimal for sparse graphs.

Dijkstra's Shortest Path Algorithm:
- Finds the shortest path from a single source vertex to all other vertices in a weighted graph with non-negative edge weights.
- Employs a Greedy Strategy using a Min-Priority Queue (Binary Heap).
- Time Complexity with Min-Heap: O((V + E) log V).
- Critical Limitation: Fails on graphs with negative edge weights (Bellman-Ford algorithm must be used instead)."""
        ),
        (
            2,
            "Propositional Logic & Truth Tables",
            "Formal Logic",
            """Propositional logic studies declarative statements that evaluate to either True (T) or False (F).
Core Logical Connectives:
1. Conjunction (AND, P ∧ Q): True only if both P and Q are True.
2. Disjunction (OR, P ∨ Q): True if at least one proposition is True.
3. Negation (NOT, ¬P): Inverts truth value.
4. Implication (IF-THEN, P → Q): Equivalent to (¬P ∨ Q). False ONLY when P is True and Q is False!
5. Biconditional (IFF, P ↔ Q): True when P and Q share identical truth values.

Important Equivalences:
- De Morgan's Laws:
  ¬(P ∧ Q) ≡ (¬P ∨ ¬Q)
  ¬(P ∨ Q) ≡ (¬P ∧ ¬Q)
- Contrapositive: (P → Q) is logically equivalent to (¬Q → ¬P)."""
        )
    ]
    cursor.executemany("INSERT INTO notes (course_id, title, topic, content) VALUES (?, ?, ?, ?);", notes)
