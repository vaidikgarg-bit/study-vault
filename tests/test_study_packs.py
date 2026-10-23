"""
Unit tests for demo study pack data verification and seeder execution.
"""

import json
import os
import sys
import pytest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "scripts"))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from seed_demo_packs import seed_packs


def test_study_packs_json_integrity():
    pack_path = os.path.join(BASE_DIR, "data", "study_packs.json")
    assert os.path.exists(pack_path)

    with open(pack_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "packs" in data
    assert len(data["packs"]) >= 2

    for p in data["packs"]:
        assert "course" in p
        assert "code" in p["course"]
        assert "title" in p["course"]
        assert "notes" in p
        assert len(p["notes"]) >= 1
        assert "content" in p["notes"][0]


def test_seed_packs_execution():
    pack_path = os.path.join(BASE_DIR, "data", "study_packs.json")
    ret = seed_packs(pack_path)
    assert ret == 0
