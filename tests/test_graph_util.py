"""
Unit and integration tests for knowledge graph builder and API endpoints.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from app import app
from graph_util import build_knowledge_graph

client = TestClient(app)


def test_build_knowledge_graph_structure():
    title = "Graph Theory & Trees"
    text = (
        "A Binary Search Tree is a tree data structure. "
        "Dijkstra Algorithm uses a Min-Heap priority queue. "
        "Tree Traversal depends on recursion."
    )
    graph = build_knowledge_graph(title, text)
    assert "nodes" in graph
    assert "edges" in graph
    assert len(graph["nodes"]) >= 2
    # Check root node
    assert any(n["category"] == "root" for n in graph["nodes"])
    # Check relation edge exists
    assert any(e["relation"] in ["is_a", "uses", "depends_on", "discusses"] for e in graph["edges"])


def test_note_knowledge_graph_endpoint():
    notes = client.get("/api/notes").json()
    note_id = notes[0]["id"]

    res = client.get(f"/api/notes/{note_id}/knowledge-graph")
    assert res.status_code == 200
    data = res.json()
    assert data["note_id"] == note_id
    assert len(data["nodes"]) >= 1


def test_course_knowledge_graph_endpoint():
    courses = client.get("/api/courses").json()
    cid = courses[0]["id"]

    res = client.get(f"/api/courses/{cid}/graph")
    assert res.status_code == 200
    data = res.json()
    assert len(data["nodes"]) >= 1
    assert any(n["category"] == "course" for n in data["nodes"])
