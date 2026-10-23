# 🎓 StudyVault

> **Course Notes Hub & AI-Powered Quiz & Flashcard Study Engine**

An intelligent campus web application built with **FastAPI**, **SQLite**, and **Tailwind CSS**. Students organize lecture notes by course code (e.g. `CS101`, `MATH200`), share study materials, and click a single button to generate interactive multiple-choice quizzes and 3D flip flashcards powered by AI.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688)
![SQLite](https://img.shields.io/badge/sqlite3-embedded-003B57)
![CI](https://github.com/vaidikgarg-bit/study-vault/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ✨ Features

- **📚 Course Vault & Document Organization**:
  - Browse notes organized by academic department and course code (`CS101`, `MATH200`, `EE102`).
  - Search by keywords, topics, or course codes with real-time client filtering.
- **⚡ AI Quiz Arena**:
  - Automatically synthesizes multiple-choice questions from study notes.
  - Interactive quiz runner with instant visual feedback (green for correct, red for incorrect) and conceptual explanations.
  - Dual-mode AI: Supports Google Gemini API online mode + built-in offline NLP heuristic extraction.
- **🗂️ 3D Spaced-Repetition Flashcards**:
  - Interactive flashcards with smooth 3D flip animations on click.
  - Active recall navigation with next/previous controls and card counters.
- **📊 Student Performance Analytics**:
  - Tracks total courses enrolled, study notes uploaded, quizzes completed, and average mastery percentage.
- **🚀 Automated CI/CD**:
  - Comprehensive unit test suite with GitHub Actions workflow running on every commit.

---

## 🛠️ Tech Stack

- **Backend**: Python 3, FastAPI, Uvicorn, Pydantic v2
- **Database**: SQLite3 (ACID compliant with foreign keys and automatic indexing)
- **AI Engine**: Google Gemini API + Offline Rule-based Heuristic NLP Fallback
- **Frontend**: Responsive Single-Page Application (SPA) with Tailwind CSS, FontAwesome 6, and custom 3D CSS transforms
- **Testing & CI**: Pytest, HTTPX TestClient, GitHub Actions

---

## 🗺️ Commit Roadmap

- [x] `docs: initialize StudyVault project specification, roadmap, and dependencies`
- [x] `feat(db): implement SQLite schema with courses, notes, quizzes, and analytics tables`
- [x] `feat(ai): build dual-mode AI quiz and flashcard generator (Gemini API + offline NLP)`
- [x] `feat(api): implement RESTful FastAPI endpoints for courses, notes, and quiz attempts`
- [x] `feat(ui): build interactive single-page dashboard with 3D flashcards and quiz arena`
- [x] `ci: add automated pytest suite and GitHub Actions workflow`
- [x] `feat(parser): add PDF document text extraction and slide reader`
- [x] `feat(algorithm): implement SuperMemo-2 spaced repetition scheduler`
- [x] `feat(api): add DELETE /api/courses/{id}`
- [x] `feat(api): add ?regenerate=true to quiz and flashcard endpoints`

---

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/vaidikgarg-bit/study-vault.git
cd study-vault
```

### 2. Set up virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Optional: Configure Gemini AI Key
*(Note: If omitted, StudyVault automatically uses its built-in offline NLP engine!)*
```bash
export GEMINI_API_KEY="your-api-key-here"
export GEMINI_MODEL="gemini-1.5-flash"  # optional, this is the default
```

### Optional: Choose the database file
StudyVault stores data in `studyvault.db` at the project root. Set `STUDYVAULT_DB` to use a different file:
```bash
export STUDYVAULT_DB="/path/to/my-vault.db"
```

### 5. Start the Web Server
```bash
uvicorn src.app:app --reload --port 8000
```
Open your browser at: **[http://localhost:8000](http://localhost:8000)**

### 6. Run Test Suite
```bash
pytest tests -v
```
Tests run against a temporary database, so your own `studyvault.db` is left untouched.

---

## 🔌 API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/courses` | List all enrolled courses with note counts |
| `POST` | `/api/courses` | Enroll a new course |
| `DELETE` | `/api/courses/{id}` | Delete a course along with its notes, quizzes and attempts |
| `GET` | `/api/courses/{id}/notes` | List notes for one course |
| `GET` | `/api/notes` | List all study notes across courses |
| `GET` | `/api/notes/{id}` | Fetch a single note |
| `POST` | `/api/notes` | Upload a new lecture note |
| `POST` | `/api/notes/upload-pdf` | Create a note from an uploaded PDF (multipart form) |
| `DELETE` | `/api/notes/{id}` | Delete a note |
| `POST` | `/api/notes/{id}/quiz` | Generate or retrieve AI quiz for a note (`?regenerate=true` forces a new one) |
| `POST` | `/api/notes/{id}/flashcards` | Generate or retrieve flashcards for a note (`?regenerate=true` forces a new deck) |
| `POST` | `/api/flashcards/review` | Compute the next SM-2 review interval for a card |
| `POST` | `/api/quiz-attempts` | Record student quiz score & time (score must be between 0 and `total_questions`) |
| `GET` | `/api/analytics` | Overall student learning metrics, including `total_flashcards` generated |

---

## 📝 Git Commit Conventions

This repository follows [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` New features or UI modes
- `fix:` Bug fixes
- `docs:` Documentation or README updates
- `test:` Unit and integration tests
- `ci:` GitHub Actions CI configuration
