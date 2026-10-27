"""
StudyVault Audio & TTS Phonetic Sentence Chunker.
Splits notes into coherent speech synthesis intervals with estimated audio timestamps.
"""

import re
from typing import List, Dict, Any
from markdown_util import strip_markdown_formatting

WORDS_PER_SECOND = 2.5  # ~150 WPM average reading speech rate


def chunk_note_for_speech(raw_text: str, max_words_per_chunk: int = 35) -> List[Dict[str, Any]]:
    """
    Cleans markdown and partitions text into acoustic clauses suitable for TTS streaming.
    Calculates estimated duration and playback time offsets.
    """
    clean_text = strip_markdown_formatting(raw_text)
    if not clean_text:
        return []

    raw_sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", clean_text) if s.strip()]
    chunks = []
    current_clause = []
    current_word_count = 0

    for sent in raw_sentences:
        words = sent.split()
        if not words:
            continue
        if current_word_count + len(words) <= max_words_per_chunk:
            current_clause.append(sent)
            current_word_count += len(words)
        else:
            if current_clause:
                clause_str = " ".join(current_clause)
                chunks.append((clause_str, current_word_count))
            current_clause = [sent]
            current_word_count = len(words)

    if current_clause:
        chunks.append((" ".join(current_clause), current_word_count))

    results = []
    current_offset = 0.0

    for idx, (text_clause, w_count) in enumerate(chunks, 1):
        duration = round(w_count / WORDS_PER_SECOND, 2)
        results.append({
            "chunk_index": idx,
            "text": text_clause,
            "word_count": w_count,
            "estimated_duration_seconds": duration,
            "start_time_offset": round(current_offset, 2)
        })
        current_offset += duration

    return results
