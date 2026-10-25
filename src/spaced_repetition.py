"""
SuperMemo-2 (SM-2) Spaced Repetition Algorithm.
Used by flashcard software like Anki to calculate optimal memory review intervals.
"""

import math
from datetime import datetime, timedelta, timezone
from typing import Dict, Any


def calculate_sm2(rating: int, repetitions: int = 0, ease_factor: float = 2.5, interval_days: int = 1, interval_modifier: float = 1.0) -> Dict[str, Any]:
    """
    Calculates next review schedule based on SuperMemo-2 algorithm.
    
    Ratings:
      1 = Again (Complete blackout, reset repetitions)
      2 = Hard (Struggled, reduce ease factor, small interval increase)
      3 = Good (Successful recall, standard interval increase)
      4 = Easy (Instant recall, boost ease factor, larger interval)
    """
    # Clamp rating between 1 and 4 (mapped to 0-5 in original SM-2)
    # Mapping: 1 -> 1, 2 -> 3, 3 -> 4, 4 -> 5
    sm2_score = {1: 1, 2: 3, 3: 4, 4: 5}.get(rating, 3)

    if sm2_score < 3:
        # Failure: reset streak
        new_repetitions = 0
        new_interval = 1
    else:
        # Success: increment repetitions and interval
        if repetitions == 0:
            new_interval = 1
        elif repetitions == 1:
            new_interval = 6
        else:
            new_interval = max(1, int(interval_days * ease_factor * interval_modifier))
        new_repetitions = repetitions + 1

    # Update Ease Factor
    # EF' = EF + (0.1 - (5 - score) * (0.08 + (5 - score) * 0.02))
    new_ease_factor = ease_factor + (0.1 - (5 - sm2_score) * (0.08 + (5 - sm2_score) * 0.02))
    new_ease_factor = max(1.3, round(new_ease_factor, 2))  # Minimum ease factor 1.3

    next_review_date = (datetime.now(timezone.utc) + timedelta(days=new_interval)).strftime("%Y-%m-%d")
    mastery = get_mastery_level(new_repetitions, new_ease_factor)

    return {
        "repetitions": new_repetitions,
        "interval_days": new_interval,
        "ease_factor": new_ease_factor,
        "due_date": next_review_date,
        "mastery_level": mastery
    }


def get_mastery_level(repetitions: int, ease_factor: float) -> str:
    """Classifies learning stage based on successful spaced repetition streak."""
    if repetitions >= 5 and ease_factor >= 2.4:
        return "Mastered"
    elif repetitions >= 3:
        return "Proficient"
    elif repetitions >= 1:
        return "Familiar"
    return "Novice"


def estimate_retention_probability(interval_days: int, days_elapsed: int, ease_factor: float = 2.5) -> float:
    """
    Estimates current memory retention percentage using the exponential Ebbinghaus forgetting curve.
    Formula: R = exp(-ln(2) * (days_elapsed / half_life))
    where half_life ~ interval_days * (ease_factor / 2.5)
    """
    if days_elapsed <= 0:
        return 100.0
    half_life = max(1.0, interval_days * (ease_factor / 2.5))
    retention = math.exp(-0.693147 * (days_elapsed / half_life)) * 100.0
    return round(max(0.0, min(100.0, retention)), 1)


def classify_card_urgency(days_overdue: int) -> str:
    """
    Classifies review urgency based on how many days past the scheduled due date.
    - 'critical': overdue by 3+ days (high forgetting probability)
    - 'due': due today or 1-2 days overdue
    - 'upcoming': due in the next 1-3 days
    - 'learning': fresh card in initial learning steps
    """
    if days_overdue >= 3:
        return "critical"
    elif days_overdue >= 0:
        return "due"
    elif days_overdue >= -3:
        return "upcoming"
    return "scheduled"
