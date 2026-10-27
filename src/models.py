"""
Pydantic data schemas for StudyVault API.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class CourseCreate(BaseModel):
    code: str = Field(..., json_schema_extra={"example": "CS101"})
    title: str = Field(..., json_schema_extra={"example": "Introduction to Computer Science"})
    department: str = Field(..., json_schema_extra={"example": "Computer Science"})
    color: Optional[str] = Field(default="indigo", json_schema_extra={"example": "indigo"})
    instructor: Optional[str] = Field(default="", json_schema_extra={"example": "Dr. Alan Turing"})
    term: Optional[str] = Field(default="Fall 2026", json_schema_extra={"example": "Fall 2026"})
    is_archived: Optional[bool] = False


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    department: Optional[str] = None
    color: Optional[str] = None
    instructor: Optional[str] = None
    term: Optional[str] = None
    is_archived: Optional[bool] = None


class CourseArchiveResponse(BaseModel):
    id: int
    is_archived: bool
    message: str



class CourseResponse(CourseCreate):
    id: int
    note_count: int = 0
    created_at: str


class NoteCreate(BaseModel):
    course_id: int
    title: str = Field(..., json_schema_extra={"example": "Binary Search Trees & Traversal Algorithms"})
    topic: str = Field(..., json_schema_extra={"example": "Data Structures"})
    content: str = Field(..., json_schema_extra={"example": "A Binary Search Tree (BST) is a node-based binary tree..."})
    tags: Optional[str] = Field(default="", json_schema_extra={"example": "trees,algorithms"})


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    topic: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[str] = None
    is_favorite: Optional[bool] = None
    is_pinned: Optional[bool] = None


class NoteResponse(NoteCreate):
    id: int
    course_code: str
    course_title: str
    is_favorite: bool = False
    is_pinned: bool = False
    tags: str = ""
    word_count: int = 0
    reading_time_mins: int = 1
    readability_score: float = 75.0
    created_at: str


class FavoriteToggleResponse(BaseModel):
    id: int
    is_favorite: bool
    message: str


class QuizOption(BaseModel):
    text: str


class QuizQuestion(BaseModel):
    id: int
    question: str
    options: List[str]
    correct_index: int
    explanation: str
    difficulty: Optional[str] = "medium"


class QuizGenerateResponse(BaseModel):
    note_id: int
    note_title: str
    questions: List[QuizQuestion]


class FlashcardItem(BaseModel):
    id: int
    front: str
    back: str
    topic: str


class FlashcardsResponse(BaseModel):
    note_id: int
    note_title: str
    flashcards: List[FlashcardItem]


class QuizAttemptCreate(BaseModel):
    note_id: int
    score: int
    total_questions: int
    time_taken_seconds: int


class QuizAttemptResponse(QuizAttemptCreate):
    id: int
    percentage: float
    created_at: str


class AnalyticsResponse(BaseModel):
    total_courses: int
    total_notes: int
    quizzes_taken: int
    average_score_percent: float
    total_flashcards_reviewed: int


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    database: str
    timestamp: str


class BulkDeleteRequest(BaseModel):
    note_ids: List[int]


class BulkDeleteResponse(BaseModel):
    deleted_count: int
    deleted_ids: List[int]


class TagCount(BaseModel):
    tag: str
    count: int


class StudySessionCreate(BaseModel):
    course_id: int
    duration_minutes: int
    session_type: str = "flashcards"  # flashcards, quiz, reading


class NoteHistoryResponse(BaseModel):
    id: int
    note_id: int
    title: str
    topic: str
    content: str
    tags: str = ""
    change_summary: Optional[str] = "Update note content"
    created_at: str


class NoteRevertResponse(BaseModel):
    id: int
    reverted_to_history_id: int
    message: str


class FlashcardImportItem(BaseModel):
    front: str
    back: str
    topic: Optional[str] = "Imported"


class FlashcardImportRequest(BaseModel):
    cards: List[FlashcardImportItem]
    replace_existing: bool = False


class FlashcardImportResponse(BaseModel):
    note_id: int
    imported_count: int
    total_cards: int
    message: str


class CourseFocusStats(BaseModel):
    course_id: int
    course_code: str
    course_title: str
    total_minutes: int
    session_count: int


class StudySessionSummary(BaseModel):
    total_focus_minutes: int
    total_sessions: int
    by_session_type: Dict[str, int]
    by_course: List[CourseFocusStats]


class ScoredNoteItem(BaseModel):
    id: int
    title: str
    topic: str
    course_code: str
    relevance_score: float
    is_pinned: bool = False
    is_favorite: bool = False


class SearchResultResponse(BaseModel):
    query: str
    total_matches: int
    results: List[ScoredNoteItem]


class PomodoroSessionCreate(BaseModel):
    course_id: int
    work_minutes: int = 25
    break_minutes: int = 5
    completed: bool = True
    task_description: Optional[str] = "Deep study focus session"


class PomodoroSessionResponse(PomodoroSessionCreate):
    id: int
    created_at: str


class PomodoroStats(BaseModel):
    total_pomodoros: int
    total_work_minutes: int
    total_break_minutes: int
    completed_rate_percent: float


class LeitnerBoxMove(BaseModel):
    card_id: int
    current_box: int = 1
    recalled_successfully: bool


class LeitnerBoxResult(BaseModel):
    card_id: int
    previous_box: int
    new_box: int
    interval_days: int
    next_review_date: str
    message: str


class LeitnerBoxSummary(BaseModel):
    box: int
    interval_days: int
    card_count: int


class CollaboratorCreate(BaseModel):
    user_email: str
    role: str = "editor"  # viewer, editor, admin


class CollaboratorResponse(CollaboratorCreate):
    id: int
    course_id: int
    added_at: str







