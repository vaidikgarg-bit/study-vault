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
- [x] `feat(nlp): add key concept and cloze deletion flashcard generator`
- [x] `feat(scheduler): implement SuperMemo-2 retention forecast and mastery levels`
- [x] `feat(export): add multi-format document exporter (Markdown, JSON, Plaintext)`
- [x] `feat(maint): add automated SQLite hot backup and vacuum script`

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

---

## 🔌 API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | System health status and DB check |
| `POST` | `/api/notes/{id}/pin` | Pin or unpin note to top of list |
| `DELETE` | `/api/notes/bulk` | Bulk delete multiple notes in one call |
| `GET` | `/api/tags` | List all unique tags and counts |
| `POST` | `/api/study-sessions` | Log study focus time session |
| `GET` | `/api/courses` | List all enrolled courses with note counts |
| `POST` | `/api/courses` | Enroll a new course |
| `PUT` | `/api/courses/{id}` | Update course title, department, or color |
| `DELETE` | `/api/courses/{id}` | Delete course and cascade notes |
| `GET` | `/api/notes` | List/search notes (`?search=`, `?course_id=`, `?favorite_only=`, `?tag=`) |
| `POST` | `/api/notes` | Upload a new lecture note |
| `PUT` | `/api/notes/{id}` | Update title, topic, content, or tags |
| `DELETE` | `/api/notes/{id}` | Delete a note and its cached quizzes |
| `POST` | `/api/notes/{id}/favorite` | Toggle note bookmark/favorite |
| `GET` | `/api/notes/{id}/export/markdown` | Download note as Markdown (.md) |
| `GET` | `/api/notes/{id}/export/json` | Download note and cached study cards as JSON |
| `GET` | `/api/notes/{id}/concepts` | Extract key technical concepts and terms |
| `POST` | `/api/notes/{id}/quiz` | Generate or retrieve AI quiz for a note |
| `POST` | `/api/notes/{id}/quiz/regenerate` | Force cache refresh and regenerate quiz |
| `POST` | `/api/notes/{id}/flashcards` | Generate or retrieve flashcards for a note |
| `POST` | `/api/notes/{id}/cloze-cards` | Generate cloze deletion fill-in-the-blank cards |
| `POST` | `/api/flashcards/review` | SuperMemo-2 (SM-2) repetition scheduler calculation |
| `POST` | `/api/quiz-attempts` | Record student quiz score & time |
| `GET` | `/api/analytics` | Overall student learning metrics |
| `GET` | `/api/analytics/activity` | Recent attempt history and streak analytics |

---

## ⌨️ Flashcard Keyboard Shortcuts

- `Space` / `Enter`: Flip flashcard
- `→` / `L`: Next card
- `←` / `H`: Previous card
- `1`: Again (reset review interval)
- `2`: Hard (small interval boost)
- `3`: Good (standard interval boost)
- `4`: Easy (exponential interval boost)

---

## 📝 Git Commit Conventions

This repository follows [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` New features or UI modes
- `fix:` Bug fixes
- `docs:` Documentation or README updates
- `test:` Unit and integration tests
- `ci:` GitHub Actions CI configuration
