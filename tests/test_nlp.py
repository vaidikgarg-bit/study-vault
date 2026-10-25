"""
Unit tests for offline NLP key concept extractor and cloze deletion card generator.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from ai_generator import (
    extract_key_concepts,
    extract_bullet_summary,
    calculate_readability_score,
    generate_cloze_flashcards,
    generate_quiz_from_notes,
    generate_flashcards_from_notes
)


def test_extract_bullet_summary():
    text = """
    A Binary Search Tree is a hierarchical structure.
    - Search: Takes O(log N) average time.
    - Insertion: Takes O(log N) average time.
    - Deletion: Takes O(log N) average time.
    """
    bullets = extract_bullet_summary(text, max_bullets=3)
    assert len(bullets) == 3
    assert any("Search" in b for b in bullets)
    assert extract_bullet_summary("") == []


def test_extract_key_concepts_empty():
    assert extract_key_concepts("") == []
    assert extract_key_concepts("   ") == []


def test_extract_key_concepts_ranking():
    text = """
    A Binary Search Tree is a tree data structure.
    In a Binary Search Tree, searching takes logarithmic time.
    Binary Search Tree algorithms are foundational.
    """
    concepts = extract_key_concepts(text, max_terms=5)
    assert len(concepts) > 0
    # "Binary Search Tree" should be detected and ranked high
    concept_names = [c["concept"] for c in concepts]
    assert any("Binary Search Tree" in name or "Tree" in name for name in concept_names)
    assert concepts[0]["relevance_score"] == 1.0


def test_extract_key_concepts_filters_stopwords():
    text = "The what when where which and the for this that with from"
    concepts = extract_key_concepts(text)
    assert len(concepts) == 0


def test_generate_cloze_flashcards_definitions():
    text = """
    Polymorphism: The provision of a single interface to entities of different types.
    Encapsulation: Bundling data and methods that manipulate data into a single unit.
    """
    cloze_cards = generate_cloze_flashcards("OOP Principles", text, max_cards=5)
    assert len(cloze_cards) >= 2
    for card in cloze_cards:
        assert "[ ... ]" in card["front"]
        assert "blank" in card
        assert card["type"] == "cloze"


def test_generate_cloze_flashcards_fallbacks():
    text = "A compiler converts high level source code into executable binary machine code."
    cloze_cards = generate_cloze_flashcards("Compilers", text, max_cards=3)
    assert len(cloze_cards) >= 1
    assert "[ ... ]" in cloze_cards[0]["front"]


def test_calculate_readability_score():
    simple = "The cat sat on the mat. The sun was hot."
    res_simple = calculate_readability_score(simple)
    assert res_simple["score"] >= 80.0
    assert res_simple["level"] == "Elementary"

    complex_txt = "Epistemological hermeneutics delineates ontological preconceptions within phenomenological discourse."
    res_complex = calculate_readability_score(complex_txt)
    assert res_complex["score"] < 40.0
    assert res_complex["level"] == "Advanced Academic"

    assert calculate_readability_score("")["score"] == 100.0


def test_quiz_question_difficulty():
    text = "Binary Search Tree: A node-based binary tree data structure with key invariant properties."
    quiz = generate_quiz_from_notes("BST", text)
    assert len(quiz) >= 1
    assert "difficulty" in quiz[0]
    assert quiz[0]["difficulty"] in ["easy", "medium", "hard"]
