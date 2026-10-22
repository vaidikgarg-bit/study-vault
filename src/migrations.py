"""
StudyVault Lightweight SQLite Migration Manager.
Handles progressive database schema versioning and deterministic schema updates.
"""

import sqlite3
from typing import List, Dict, Any, Callable

MIGRATION_REGISTRY: List[Dict[str, Any]] = []


def register_migration(version: int, name: str):
    """Decorator to register a migration function."""
    def decorator(fn: Callable[[sqlite3.Connection], None]):
        MIGRATION_REGISTRY.append({
            "version": version,
            "name": name,
            "fn": fn
        })
        MIGRATION_REGISTRY.sort(key=lambda m: m["version"])
        return fn
    return decorator


def get_applied_migrations(conn: sqlite3.Connection) -> List[int]:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    rows = conn.execute("SELECT version FROM schema_migrations ORDER BY version ASC;").fetchall()
    return [r[0] for r in rows]


def run_pending_migrations(conn: sqlite3.Connection) -> List[str]:
    """Applies all registered migrations that have not yet been run."""
    applied = set(get_applied_migrations(conn))
    applied_names = []

    for mig in MIGRATION_REGISTRY:
        ver = mig["version"]
        name = mig["name"]
        if ver not in applied:
            # Execute migration in transaction
            with conn:
                mig["fn"](conn)
                conn.execute(
                    "INSERT INTO schema_migrations (version, name) VALUES (?, ?);",
                    (ver, name)
                )
            applied_names.append(f"{ver}_{name}")

    return applied_names
