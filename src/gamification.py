"""
StudyVault Gamification & Badge Milestone Engine.
Computes learner achievements based on real-time activity and vault metrics.
"""

from typing import List, Dict, Any


BADGE_DEFINITIONS = [
    {
        "id": "first_note",
        "title": "Vault Pioneer",
        "description": "Created your very first lecture note in the vault.",
        "icon": "fa-pen-nib",
        "category": "notes",
        "threshold": 1
    },
    {
        "id": "scholar",
        "title": "Knowledge Hoarder",
        "description": "Compiled 5 or more comprehensive study notes.",
        "icon": "fa-book-open",
        "category": "notes",
        "threshold": 5
    },
    {
        "id": "multi_course",
        "title": "Renaissance Student",
        "description": "Enrolled in 3 or more academic courses across departments.",
        "icon": "fa-graduation-cap",
        "category": "courses",
        "threshold": 3
    },
    {
        "id": "quiz_gladiator",
        "title": "Quiz Gladiator",
        "description": "Successfully completed 3 or more AI quiz evaluations.",
        "icon": "fa-trophy",
        "category": "quiz",
        "threshold": 3
    },
    {
        "id": "mastery_mind",
        "title": "High Achiever",
        "description": "Maintained an average quiz score of 80% or higher.",
        "icon": "fa-medal",
        "category": "quiz",
        "threshold": 80.0
    },
    {
        "id": "deep_focus",
        "title": "Focus Champion",
        "description": "Logged at least 60 minutes of active learning sessions.",
        "icon": "fa-hourglass-half",
        "category": "focus",
        "threshold": 60
    }
]


def evaluate_badges(metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Evaluates earned badges against student learning metrics.
    metrics dict expects:
      total_notes: int
      total_courses: int
      quizzes_taken: int
      average_score_percent: float
      total_focus_minutes: int
    """
    results = []
    notes_count = metrics.get("total_notes", 0)
    courses_count = metrics.get("total_courses", 0)
    quizzes_count = metrics.get("quizzes_taken", 0)
    avg_score = metrics.get("average_score_percent", 0.0)
    focus_mins = metrics.get("total_focus_minutes", 0)

    for badge in BADGE_DEFINITIONS:
        b_id = badge["id"]
        unlocked = False
        progress = 0

        if b_id == "first_note":
            unlocked = notes_count >= 1
            progress = min(100, int((notes_count / 1) * 100))
        elif b_id == "scholar":
            unlocked = notes_count >= 5
            progress = min(100, int((notes_count / 5) * 100))
        elif b_id == "multi_course":
            unlocked = courses_count >= 3
            progress = min(100, int((courses_count / 3) * 100))
        elif b_id == "quiz_gladiator":
            unlocked = quizzes_count >= 3
            progress = min(100, int((quizzes_count / 3) * 100))
        elif b_id == "mastery_mind":
            unlocked = quizzes_count >= 1 and avg_score >= 80.0
            progress = min(100, int((avg_score / 80.0) * 100)) if quizzes_count >= 1 else 0
        elif b_id == "deep_focus":
            unlocked = focus_mins >= 60
            progress = min(100, int((focus_mins / 60) * 100))

        results.append({
            **badge,
            "unlocked": unlocked,
            "progress_percent": progress
        })

    return results
