"""
Unit tests for SuperMemo-2 (SM-2) spaced repetition algorithm.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from spaced_repetition import calculate_sm2


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
