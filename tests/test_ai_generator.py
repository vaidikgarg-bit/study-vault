"""
Unit tests for the Gemini client wiring in the AI study engine.
"""

import os
import sys
import json
import httpx
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import ai_generator


def _capture_gemini_request(monkeypatch):
    """Routes httpx.Client through a mock transport and records the outgoing request."""
    captured = {}
    body = {"candidates": [{"content": {"parts": [{"text": json.dumps([{"id": 1}])}]}}]}

    def handler(request):
        captured["request"] = request
        return httpx.Response(200, json=body)

    real_client = httpx.Client
    monkeypatch.setattr(ai_generator.httpx, "Client",
                        lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw))
    return captured


def test_gemini_key_sent_in_header_not_url(monkeypatch):
    captured = _capture_gemini_request(monkeypatch)
    ai_generator._call_gemini_json("prompt", "secret-key")

    request = captured["request"]
    assert request.headers["x-goog-api-key"] == "secret-key"
    assert "secret-key" not in str(request.url)


def test_gemini_model_can_be_overridden(monkeypatch):
    captured = _capture_gemini_request(monkeypatch)
    monkeypatch.setenv("GEMINI_MODEL", "gemini-test-model")
    ai_generator._call_gemini_json("prompt", "k")
    assert "/models/gemini-test-model:generateContent" in str(captured["request"].url)


def test_falls_back_to_offline_engine_when_gemini_fails(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "k")

    def boom(prompt, api_key):
        raise httpx.ConnectError("offline")
    monkeypatch.setattr(ai_generator, "_call_gemini_json", boom)

    questions = ai_generator.generate_quiz_from_notes("Stacks", "Stack: a last-in, first-out collection of items.")
    assert len(questions) >= 1
