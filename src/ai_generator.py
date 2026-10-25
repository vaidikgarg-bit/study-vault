"""
AI Study Engine: Generates intelligent multiple-choice quizzes and flashcards from student notes.
Features Gemini API integration with an offline rule-based NLP extraction fallback.
"""

import json
import os
import re
from typing import List, Dict, Any
import httpx


STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both",
    "but", "by", "can", "can't", "cannot", "could", "did", "do", "does", "doing", "don't", "down",
    "during", "each", "few", "for", "from", "further", "had", "has", "have", "having", "he",
    "her", "here", "hers", "herself", "him", "himself", "his", "how", "i", "if", "in", "into",
    "is", "it", "its", "itself", "let's", "me", "more", "most", "must", "my", "myself", "no",
    "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours",
    "ourselves", "out", "over", "own", "same", "she", "should", "so", "some", "such", "than",
    "that", "the", "their", "theirs", "them", "themselves", "then", "there", "these", "they",
    "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "we", "were",
    "what", "when", "where", "which", "while", "who", "whom", "why", "with", "would", "you", "your"
}


def extract_key_concepts(text: str, max_terms: int = 8) -> List[Dict[str, Any]]:
    """
    Extracts key concepts, technical terms, and high-frequency subject keywords from study text.
    """
    if not text:
        return []

    # Tokenize words while preserving hyphens
    tokens = re.findall(r"\b[A-Za-z][A-Za-z0-9\-]{2,}\b", text)
    term_counts: Dict[str, int] = {}

    for token in tokens:
        lower = token.lower()
        if lower in STOPWORDS or len(lower) < 4:
            continue
        term_counts[lower] = term_counts.get(lower, 0) + 1

    # Also detect multi-word capitalized phrases (e.g., "Binary Search Tree", "Dijkstra's Algorithm")
    phrases = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b", text)
    for phrase in phrases:
        p_clean = phrase.strip()
        if len(p_clean) > 5:
            term_counts[p_clean] = term_counts.get(p_clean, 0) + 2

    if not term_counts:
        return []

    sorted_terms = sorted(term_counts.items(), key=lambda x: x[1], reverse=True)[:max_terms]
    max_freq = sorted_terms[0][1] if sorted_terms else 1

    return [
        {
            "concept": term.title() if term.islower() else term,
            "frequency": count,
            "relevance_score": round(min(1.0, count / max_freq), 2)
        }
        for term, count in sorted_terms
    ]


def extract_bullet_summary(text: str, max_bullets: int = 4) -> List[str]:
    """
    Extracts core summary bullet takeaways from study text using sentence ranking.
    Prioritizes definition statements, complexity notation, and theorem invariants.
    """
    if not text:
        return []

    bullets = []
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # Priority 1: Definitions and numbered lists
    for line in lines:
        if line.startswith(("-", "*", "•")) or re.match(r"^\d+\.", line):
            cleaned = re.sub(r"^[-*•\d\.]+\s*", "", line).strip()
            if len(cleaned) > 15 and cleaned not in bullets:
                bullets.append(cleaned)
        elif ":" in line and not line.lower().startswith("note:"):
            parts = line.split(":", 1)
            if len(parts[0]) < 40 and len(parts[1].strip()) > 15:
                bullets.append(line)

        if len(bullets) >= max_bullets:
            break

    # Priority 2: Fallback to sentences if list items were scarce
    if len(bullets) < max_bullets:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        for s in sentences:
            s_clean = s.strip()
            if len(s_clean) > 25 and s_clean not in bullets:
                bullets.append(s_clean)
            if len(bullets) >= max_bullets:
                break

    return bullets[:max_bullets]


def generate_quiz_from_notes(note_title: str, note_content: str) -> List[Dict[str, Any]]:
    """Generates structured multiple-choice questions from study notes."""
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            return _generate_quiz_gemini(note_title, note_content, api_key)
        except Exception:
            # Fall back to offline heuristic engine
            pass
    return _generate_quiz_offline(note_title, note_content)


def generate_flashcards_from_notes(note_title: str, note_content: str) -> List[Dict[str, Any]]:
    """Generates spaced-repetition flashcards from study notes."""
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            return _generate_flashcards_gemini(note_title, note_content, api_key)
        except Exception:
            pass
    return _generate_flashcards_offline(note_title, note_content)


# ---------------------------------------------------------------------------
# Offline Heuristic NLP Engine (Zero API Key required, 100% Offline Ready)
# ---------------------------------------------------------------------------

def _generate_quiz_offline(title: str, text: str) -> List[Dict[str, Any]]:
    questions = []
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # Extract definitions and facts
    for idx, line in enumerate(lines):
        # Look for "Term: Definition" or "Term is Definition"
        match_colon = re.match(r"^([A-Za-z0-9\s\-\(\)\']+):\s*(.+)$", line)
        match_is = re.match(r"^([A-Za-z0-9\s\-\(\)\']+)\s+(is|are|consist of|finds)\s+(.+)$", line, re.IGNORECASE)

        if match_colon:
            term = match_colon.group(1).strip()
            fact = match_colon.group(2).strip()
            if len(term) > 3 and len(fact) > 10 and not term.startswith("Note"):
                correct = fact
                distractors = [
                    f"Inverts the traversal order and operates in O(N!) factorial space.",
                    f"Requires O(V^3) time complexity and fails on sorted inputs.",
                    f"Only applies to disconnected graphs and static array buffers."
                ]
                options = [correct] + distractors
                # Shuffle deterministically based on string length
                shift = len(term) % 4
                options = options[shift:] + options[:shift]
                correct_idx = options.index(correct)

                questions.append({
                    "id": len(questions) + 1,
                    "question": f"Which of the following accurately describes '{term}'?",
                    "options": options,
                    "correct_index": correct_idx,
                    "explanation": f"According to the notes: {term} — {correct}",
                    "difficulty": "medium" if len(term) < 15 else "hard"
                })

        elif match_is and len(questions) < 5:
            term = match_is.group(1).strip()
            verb = match_is.group(2).strip()
            fact = match_is.group(3).strip()
            if len(term) > 3 and len(fact) > 15:
                correct = f"{verb} {fact}"
                distractors = [
                    "evaluates to False under all circumstances without verification.",
                    "is bounded by O(1) constant time but leaks memory across threads.",
                    "requires external hardware interrupts to complete execution."
                ]
                options = [correct] + distractors
                shift = len(fact) % 4
                options = options[shift:] + options[:shift]
                correct_idx = options.index(correct)

                questions.append({
                    "id": len(questions) + 1,
                    "question": f"What is true regarding '{term}'?",
                    "options": options,
                    "correct_index": correct_idx,
                    "explanation": f"Key takeaway: {term} {correct}"
                })

        if len(questions) >= 5:
            break

    # If document was too brief or unstructured, provide high-yield conceptual questions
    if len(questions) < 3:
        questions.append({
            "id": len(questions) + 1,
            "question": f"What is the primary topic covered in '{title}'?",
            "options": [
                f"Core foundations, definitions, and key properties of {title}.",
                "Hardware assembly language registers.",
                "CSS box model positioning and responsive flexbox.",
                "Database relational calculus and BCNF normalization."
            ],
            "correct_index": 0,
            "explanation": f"This note focuses directly on the core principles of {title}."
        })
        questions.append({
            "id": len(questions) + 1,
            "question": "What is the recommended approach when reviewing this material before an exam?",
            "options": [
                "Review the definitions, understand worst-case edge cases, and test recall with flashcards.",
                "Memorize line numbers without understanding algorithmic properties.",
                "Skip practice problems and rely purely on passive reading.",
                "Discard notes after a single initial lecture."
            ],
            "correct_index": 0,
            "explanation": "Active recall and spaced testing are scientifically proven to maximize exam performance."
        })

    return questions


def _generate_flashcards_offline(title: str, text: str) -> List[Dict[str, Any]]:
    cards = []
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    for line in lines:
        match_colon = re.match(r"^([A-Za-z0-9\s\-\(\)\']+):\s*(.+)$", line)
        if match_colon:
            front = match_colon.group(1).strip()
            back = match_colon.group(2).strip()
            if len(front) > 3 and len(back) > 8:
                cards.append({
                    "id": len(cards) + 1,
                    "front": front,
                    "back": back,
                    "topic": title
                })
        elif "Algorithm" in line or "Invariant" in line or "Complexity" in line:
            cards.append({
                "id": len(cards) + 1,
                "front": line.split(".")[0],
                "back": line,
                "topic": title
            })

        if len(cards) >= 6:
            break

    if not cards:
        cards.append({
            "id": 1,
            "front": f"Overview of {title}",
            "back": text[:200] + ("..." if len(text) > 200 else ""),
            "topic": title
        })

    return cards


def generate_cloze_flashcards(title: str, text: str, max_cards: int = 6) -> List[Dict[str, Any]]:
    """
    Generates fill-in-the-blank (Cloze Deletion) flashcards for active recall.
    Identifies high-value sentences and blanks out key technical entities.
    """
    cloze_cards = []
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # Pattern for definitions: "Term: Definition" or "Term is ..."
    for line in lines:
        match_colon = re.match(r"^([A-Za-z0-9\s\-\(\)\']+):\s*(.+)$", line)
        if match_colon:
            term = match_colon.group(1).strip()
            fact = match_colon.group(2).strip()
            if len(term) >= 3 and len(fact) >= 15:
                cloze_cards.append({
                    "id": len(cloze_cards) + 1,
                    "front": f"[ ... ] : {fact}",
                    "back": f"**{term}**\n\n{fact}",
                    "blank": term,
                    "type": "cloze",
                    "topic": title
                })
        else:
            # Check for key terms inside informative sentences
            match_keywords = re.findall(r"\b([A-Z][a-z0-9\-]+(?:\s+[A-Z][a-z0-9\-]+)*)\b", line)
            target_kw = None
            for kw in match_keywords:
                if len(kw) > 4 and kw.lower() not in STOPWORDS and len(line) > len(kw) + 15:
                    target_kw = kw
                    break

            if not target_kw:
                # Fallback to substantive words (length >= 6) not in stopwords
                candidate_words = [w for w in re.findall(r"\b[A-Za-z\-]{6,}\b", line) if w.lower() not in STOPWORDS]
                if candidate_words:
                    target_kw = candidate_words[0]

            if target_kw:
                cloze_sentence = line.replace(target_kw, "[ ... ]", 1)
                cloze_cards.append({
                    "id": len(cloze_cards) + 1,
                    "front": cloze_sentence,
                    "back": f"Missing term: **{target_kw}**\n\nFull statement: {line}",
                    "blank": target_kw,
                    "type": "cloze",
                    "topic": title
                })

        if len(cloze_cards) >= max_cards:
            break

    return cloze_cards


# ---------------------------------------------------------------------------
# Gemini AI Online Engine (Activated when GEMINI_API_KEY is configured)
# ---------------------------------------------------------------------------

def _generate_quiz_gemini(title: str, text: str, api_key: str) -> List[Dict[str, Any]]:
    prompt = f"""You are a university professor creating an exam quiz from student notes.
Note Title: {title}
Note Content:
{text}

Generate 5 high-yield multiple-choice questions in strict JSON format:
[
  {{
    "id": 1,
    "question": "Question text",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_index": 0,
    "explanation": "Brief explanation why this option is correct."
  }}
]
Return ONLY valid JSON array with no extra markdown or text."""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}
    }
    with httpx.Client(timeout=15.0) as client:
        res = client.post(url, json=payload)
        res.raise_for_status()
        data = res.json()
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(raw_text)


def _generate_flashcards_gemini(title: str, text: str, api_key: str) -> List[Dict[str, Any]]:
    prompt = f"""You are an expert tutor creating study flashcards from student notes.
Note Title: {title}
Note Content:
{text}

Generate 6 spaced-repetition flashcards in strict JSON format:
[
  {{
    "id": 1,
    "front": "Concept or Question",
    "back": "Clear, concise definition or answer",
    "topic": "{title}"
  }}
]
Return ONLY valid JSON array with no extra markdown or text."""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}
    }
    with httpx.Client(timeout=15.0) as client:
        res = client.post(url, json=payload)
        res.raise_for_status()
        data = res.json()
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(raw_text)


def calculate_readability_score(text: str) -> dict:
    """
    Calculates reading ease and grade level based on the Flesch-Kincaid index.
    Formula: 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
    """
    if not text or not text.strip():
        return {"score": 100.0, "grade": "Easy", "level": "Elementary"}

    words = [w for w in re.findall(r"\b[A-Za-z]+\b", text)]
    if not words:
        return {"score": 100.0, "grade": "Easy", "level": "Elementary"}

    sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
    num_sentences = max(1, len(sentences))
    num_words = len(words)

    # Approximate syllable count (vowel clusters)
    syllable_count = 0
    for w in words:
        syl = len(re.findall(r"[aeiouy]+", w.lower()))
        syllable_count += max(1, syl)

    score = 206.835 - 1.015 * (num_words / num_sentences) - 84.6 * (syllable_count / num_words)
    clamped = round(max(0.0, min(100.0, score)), 1)

    if clamped >= 80:
        level = "Elementary"
    elif clamped >= 60:
        level = "Intermediate"
    elif clamped >= 40:
        level = "College"
    else:
        level = "Advanced Academic"

    return {"score": clamped, "level": level}
