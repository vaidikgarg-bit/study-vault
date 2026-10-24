#!/usr/bin/env python3
"""
StudyVault SQLite Database Backup & Maintenance Utility.
Performs hot backups using SQLite online backup API and vacuums database.
"""

import os
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "studyvault.db"
BACKUP_DIR = BASE_DIR / "backups"


def perform_backup(source_db_path=DB_PATH, backup_dir=BACKUP_DIR) -> str:
    if not os.path.exists(source_db_path):
        raise FileNotFoundError(f"Database not found at {source_db_path}")

    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"studyvault_backup_{timestamp}.db"

    # Online backup using SQLite Backup API
    src = sqlite3.connect(source_db_path)
    dst = sqlite3.connect(backup_file)
    with dst:
        src.backup(dst, pages=100)
    dst.close()

    # Run vacuum on source database
    src.execute("VACUUM;")
    src.close()

    return str(backup_file)


if __name__ == "__main__":
    try:
        dest = perform_backup()
        print(f"✅ Successfully backed up database to: {dest}")
    except Exception as e:
        print(f"❌ Backup failed: {e}", file=sys.stderr)
        sys.exit(1)
