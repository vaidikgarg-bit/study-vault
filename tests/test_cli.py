"""
Unit tests for StudyVault CLI tool (scripts/vault_cli.py).
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from vault_cli import build_parser, main


def test_cli_parser_commands():
    parser = build_parser()
    args_status = parser.parse_args(["status"])
    assert args_status.command == "status"

    args_courses = parser.parse_args(["courses", "--archived"])
    assert args_courses.command == "courses"
    assert args_courses.archived is True

    args_notes = parser.parse_args(["notes", "--course", "CS101", "--favorites"])
    assert args_notes.command == "notes"
    assert args_notes.course == "CS101"
    assert args_notes.favorites is True

    args_stats = parser.parse_args(["stats"])
    assert args_stats.command == "stats"


def test_cli_execution_status(capsys):
    ret = main(["status"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "healthy" in captured.out


def test_cli_execution_courses(capsys):
    ret = main(["courses"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "CODE" in captured.out
    assert "CS101" in captured.out


def test_cli_execution_notes(capsys):
    ret = main(["notes", "--course", "CS101"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "CS101" in captured.out


def test_cli_execution_stats(capsys):
    ret = main(["stats"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Database Metrics" in captured.out
