"""
Unit and integration tests for SQLite schema migration manager.
"""

import os
import sqlite3
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from app import app
from migrations import (
    get_applied_migrations,
    run_pending_migrations,
    register_migration,
    MIGRATION_REGISTRY
)

client = TestClient(app)


def test_migrations_api_status():
    res = client.get("/api/system/migrations")
    assert res.status_code == 200
    data = res.json()
    assert data["total_registered"] >= 3
    assert data["total_applied"] >= 3
    assert 1 in data["applied_versions"]
    assert 2 in data["applied_versions"]
    assert 3 in data["applied_versions"]


def test_migration_runner_idempotence():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE notes (id INT, course_id INT, is_favorite INT);")
    conn.execute("CREATE TABLE courses (id INT, is_archived INT);")
    conn.execute("CREATE TABLE note_history (id INT, note_id INT);")

    # First run applies all
    applied_first = run_pending_migrations(conn)
    assert len(applied_first) >= 3

    # Second run should be a no-op
    applied_second = run_pending_migrations(conn)
    assert len(applied_second) == 0

    conn.close()
