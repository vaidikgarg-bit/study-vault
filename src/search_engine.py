"""
StudyVault In-Memory Relevance Search & Scoring Engine.
Calculates tf-idf style weighted relevance scores across notes for academic search queries.
"""

import re
from typing import List, Dict, Any


def score_note_relevance(query: str, note: Dict[str, Any]) -> float:
    """
    Computes an empirical relevance score between a search query and a note.
    Weights:
      - Title exact phrase: +10.0
      - Title token match: +4.0 per token
      - Topic token match: +3.0 per token
      - Tag exact match: +2.5
      - Content token occurrence: +0.5 (capped at 5.0)
      - Pinned boost: +2.0
      - Favorite boost: +1.0
    """
    if not query or not query.strip():
        return 0.0

    q_lower = query.strip().lower()
    tokens = [t for t in re.findall(r"\b\w+\b", q_lower) if len(t) >= 2]
    if not tokens:
        return 0.0

    score = 0.0
    title_lower = (note.get("title") or "").lower()
    topic_lower = (note.get("topic") or "").lower()
    tags_lower = (note.get("tags") or "").lower()
    content_lower = (note.get("content") or "").lower()

    # Exact full query match in title
    if q_lower in title_lower:
        score += 10.0

    # Token matches
    content_hits = 0
    for t in tokens:
        if t in title_lower:
            score += 4.0
        if t in topic_lower:
            score += 3.0
        if t in tags_lower:
            score += 2.5
        content_hits += content_lower.count(t)

    score += min(5.0, content_hits * 0.5)

    # Contextual boosts
    if note.get("is_pinned"):
        score += 2.0
    if note.get("is_favorite"):
        score += 1.0

    return round(score, 2)


def rank_notes(query: str, notes: List[Dict[str, Any]], min_score: float = 1.0) -> List[Dict[str, Any]]:
    """Filters and ranks a collection of notes against a search query by score descending."""
    scored = []
    for note in notes:
        s = score_note_relevance(query, note)
        if s >= min_score:
            scored.append({**note, "relevance_score": s})

    scored.sort(key=lambda x: x["relevance_score"], reverse=True)
    return scored
