# 🔌 StudyVault REST API Developer Guide

Quick reference and `curl` examples for interacting with the StudyVault HTTP API.

Base URL: `http://localhost:8000`

---

## 📚 1. Courses

### List Enrolled Courses
```bash
curl -X GET "http://localhost:8000/api/courses?include_archived=true"
```

### Enroll a New Course
```bash
curl -X POST "http://localhost:8000/api/courses" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "CS201",
    "title": "Algorithms & Complexity",
    "department": "Computer Science",
    "color": "indigo",
    "instructor": "Dr. Donald Knuth",
    "term": "Fall 2026"
  }'
```

### Archive / Restore Course
```bash
curl -X POST "http://localhost:8000/api/courses/1/archive"
```

---

## 📝 2. Study Notes

### Upload Note
```bash
curl -X POST "http://localhost:8000/api/notes" \
  -H "Content-Type: application/json" \
  -d '{
    "course_id": 1,
    "title": "Asymptotic Big-O Notation",
    "topic": "Complexity Theory",
    "content": "Big-O notation describes the limiting behavior of a function.",
    "tags": "algorithms,big-o"
  }'
```

### Ranked Relevance Search
```bash
curl -X GET "http://localhost:8000/api/search?q=Binary+Search&limit=10"
```

### Revision History & Rollback
```bash
# Get history revisions
curl -X GET "http://localhost:8000/api/notes/1/history"

# Revert to revision #1
curl -X POST "http://localhost:8000/api/notes/1/revert/1"
```

---

## ⚡ 3. AI Quiz & Spaced Repetition

### Generate AI Quiz
```bash
curl -X POST "http://localhost:8000/api/notes/1/quiz"
```

### SM-2 Flashcard Review Calculation
```bash
curl -X POST "http://localhost:8000/api/flashcards/review?rating=3&repetitions=1&ease_factor=2.5&interval_days=1"
```

### Export to Anki TSV Deck
```bash
curl -X GET "http://localhost:8000/api/notes/1/export/anki" -o deck.tsv
```

---

## ⏱️ 4. Focus & Pomodoro Sessions

### Log Pomodoro Interval
```bash
curl -X POST "http://localhost:8000/api/pomodoro/sessions" \
  -H "Content-Type: application/json" \
  -d '{
    "course_id": 1,
    "work_minutes": 25,
    "break_minutes": 5,
    "completed": true,
    "task_description": "Review Chapter 3"
  }'
```

### Retrieve Achievement Badges
```bash
curl -X GET "http://localhost:8000/api/analytics/badges"
```
