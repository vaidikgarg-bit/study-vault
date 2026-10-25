"""
Pydantic data schemas for StudyVault API.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class CourseCreate(BaseModel):
    code: str = Field(..., json_schema_extra={"example": "CS101"})
    title: str = Field(..., json_schema_extra={"example": "Introduction to Computer Science"})
    department: str = Field(..., json_schema_extra={"example": "Computer Science"})
    color: Optional[str] = Field(default="indigo", json_schema_extra={"example": "indigo"})
    instructor: Optional[str] = Field(default="", json_schema_extra={"example": "Dr. Alan Turing"})
    term: Optional[str] = Field(default="Fall 2026", json_schema_extra={"example": "Fall 2026"})


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    department: Optional[str] = None
    color: Optional[str] = None


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
