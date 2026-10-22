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

    return parser


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

    return 0


if __name__ == "__main__":
    sys.exit(main())
