"""
Unit tests for SuperMemo-2 (SM-2) spaced repetition algorithm.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from spaced_repetition import (
    calculate_sm2,
    estimate_retention_probability,
    classify_card_urgency,
    get_mastery_level,
    project_retention_curve,
    calculate_fsrs_metrics
)


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


def test_get_mastery_level():
    assert get_mastery_level(0, 2.5) == "Novice"
    assert get_mastery_level(1, 2.5) == "Familiar"
    assert get_mastery_level(3, 2.5) == "Proficient"
    assert get_mastery_level(5, 2.5) == "Mastered"
    assert get_mastery_level(5, 2.0) == "Proficient"


def test_classify_card_urgency():
    assert classify_card_urgency(days_overdue=5) == "critical"
    assert classify_card_urgency(days_overdue=0) == "due"
    assert classify_card_urgency(days_overdue=-2) == "upcoming"
    assert classify_card_urgency(days_overdue=-10) == "scheduled"


def test_sm2_interval_modifier():
    # 2.0x modifier doubles calculated interval
    standard = calculate_sm2(rating=3, repetitions=2, ease_factor=2.5, interval_days=6, interval_modifier=1.0)
    doubled = calculate_sm2(rating=3, repetitions=2, ease_factor=2.5, interval_days=6, interval_modifier=2.0)
    assert doubled["interval_days"] >= standard["interval_days"] * 2 - 1


def test_retention_curve_projection():
    curve = project_retention_curve(interval_days=7, ease_factor=2.5, days_ahead=10)
    assert len(curve) == 11  # days 0 through 10
    assert curve[0]["day"] == 0
    assert curve[0]["retention_percent"] == 100.0
    assert curve[0]["needs_review"] is False
    assert curve[-1]["day"] == 10
    assert curve[-1]["retention_percent"] < curve[0]["retention_percent"]


def test_calculate_fsrs_metrics():
    # Day 0: 100% retrievability
    m0 = calculate_fsrs_metrics(repetitions=2, interval_days=6, ease_factor=2.5, days_elapsed=0)
    assert m0["retrievability_percent"] == 100.0
    assert m0["retention_status"] == "Optimal"
    assert m0["stability_days"] > 6.0

    # With elapsed days, retrievability drops
    m_later = calculate_fsrs_metrics(repetitions=2, interval_days=6, ease_factor=2.5, days_elapsed=15)
    assert m_later["retrievability_percent"] < 100.0


