"""
Unit tests for SQLite database backup utility.
"""

import os
import sys
import tempfile
import sqlite3
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from backup_db import perform_backup
from pathlib import Path


def test_perform_backup_creates_valid_sqlite():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        db_file = tmp_path / "test.db"
        backup_dir = tmp_path / "backups"

        # Initialize mock DB
        conn = sqlite3.connect(db_file)
        conn.execute("CREATE TABLE mock (id INT, name TEXT);")
        conn.execute("INSERT INTO mock VALUES (1, 'StudyVault');")
        conn.commit()
        conn.close()

        # Perform backup
        backup_path = perform_backup(source_db_path=db_file, backup_dir=backup_dir)
        assert os.path.exists(backup_path)

        # Verify backup contents
        b_conn = sqlite3.connect(backup_path)
        row = b_conn.execute("SELECT name FROM mock WHERE id = 1;").fetchone()
        b_conn.close()
        assert row[0] == "StudyVault"
