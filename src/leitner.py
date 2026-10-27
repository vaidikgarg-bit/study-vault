"""
StudyVault Leitner 5-Box Spaced Repetition Scheduling Engine.
Implements classic physical-to-digital flashcard box interval progression.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any

LEITNER_BOX_INTERVALS = {
    1: 1,    # Box 1: Daily review
    2: 2,    # Box 2: Every 2 days
    3: 5,    # Box 3: Every 5 days
    4: 9,    # Box 4: Every 9 days
    5: 14    # Box 5: Every 2 weeks (Mastered)
}


def calculate_leitner_transition(current_box: int, recalled_successfully: bool) -> Dict[str, Any]:
    """
    Computes box promotion or demotion under the Leitner System.
    Success: Advance to next box (max Box 5).
    Failure: Demote back to Box 1 for intensive relearning.
    """
    box = max(1, min(5, current_box))

    if recalled_successfully:
        new_box = min(5, box + 1)
        action = "promoted" if new_box > box else "maintained at maximum"
    else:
        new_box = 1
        action = "reset to Box 1"

    interval_days = LEITNER_BOX_INTERVALS[new_box]
    next_review = (datetime.now(timezone.utc) + timedelta(days=interval_days)).strftime("%Y-%m-%d")

    return {
        "previous_box": box,
        "new_box": new_box,
        "interval_days": interval_days,
        "next_review_date": next_review,
        "action": action
    }
