"""
SuperMemo-2 (SM-2) Spaced Repetition Algorithm.
Used by flashcard software like Anki to calculate optimal memory review intervals.
"""

from datetime import datetime, timedelta
from typing import Dict, Any


def calculate_sm2(rating: int, repetitions: int = 0, ease_factor: float = 2.5, interval_days: int = 1) -> Dict[str, Any]:
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
            new_interval = max(1, int(interval_days * ease_factor))
        new_repetitions = repetitions + 1

    # Update Ease Factor
    # EF' = EF + (0.1 - (5 - score) * (0.08 + (5 - score) * 0.02))
    new_ease_factor = ease_factor + (0.1 - (5 - sm2_score) * (0.08 + (5 - sm2_score) * 0.02))
    new_ease_factor = max(1.3, round(new_ease_factor, 2))  # Minimum ease factor 1.3

    next_review_date = (datetime.utcnow() + timedelta(days=new_interval)).strftime("%Y-%m-%d")

    return {
        "repetitions": new_repetitions,
        "interval_days": new_interval,
        "ease_factor": new_ease_factor,
        "due_date": next_review_date
    }
