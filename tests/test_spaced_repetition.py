"""
Unit tests for SuperMemo-2 (SM-2) spaced repetition algorithm.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from spaced_repetition import calculate_sm2, estimate_retention_probability, classify_card_urgency


def test_sm2_first_review_success():
    result = calculate_sm2(rating=3, repetitions=0, ease_factor=2.5, interval_days=1)
    assert result["repetitions"] == 1
    assert result["interval_days"] == 1
    assert result["ease_factor"] >= 2.5


def test_sm2_second_review_success():
    result = calculate_sm2(rating=3, repetitions=1, ease_factor=2.5, interval_days=1)
    assert result["repetitions"] == 2
    assert result["interval_days"] == 6


def test_sm2_subsequent_review_multiplies_by_ease():
    result = calculate_sm2(rating=4, repetitions=2, ease_factor=2.5, interval_days=6)
    assert result["repetitions"] == 3
    assert result["interval_days"] >= 15  # 6 * 2.5+


def test_sm2_failure_resets_interval():
    result = calculate_sm2(rating=1, repetitions=4, ease_factor=2.5, interval_days=30)
    assert result["repetitions"] == 0
    assert result["interval_days"] == 1


def test_retention_probability():
    # Day 0: 100% retention
    assert estimate_retention_probability(interval_days=10, days_elapsed=0) == 100.0
    # Day equal to interval: ~50% retention
    ret = estimate_retention_probability(interval_days=10, days_elapsed=10, ease_factor=2.5)
    assert 45.0 <= ret <= 55.0
    # Long elapsed time decays significantly
    assert estimate_retention_probability(interval_days=5, days_elapsed=50) < 5.0


def test_classify_card_urgency():
    assert classify_card_urgency(days_overdue=5) == "critical"
    assert classify_card_urgency(days_overdue=0) == "due"
    assert classify_card_urgency(days_overdue=-2) == "upcoming"
    assert classify_card_urgency(days_overdue=-10) == "scheduled"
