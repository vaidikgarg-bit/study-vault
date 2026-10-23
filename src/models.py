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


class CourseResponse(CourseCreate):
    id: int
    note_count: int = 0
    created_at: str


class NoteCreate(BaseModel):
    course_id: int
    title: str = Field(..., json_schema_extra={"example": "Binary Search Trees & Traversal Algorithms"})
    topic: str = Field(..., json_schema_extra={"example": "Data Structures"})
    content: str = Field(..., json_schema_extra={"example": "A Binary Search Tree (BST) is a node-based binary tree..."})


class NoteResponse(NoteCreate):
    id: int
    course_code: str
    course_title: str
    created_at: str


class QuizOption(BaseModel):
    text: str


class QuizQuestion(BaseModel):
    id: int
    question: str
    options: List[str]
    correct_index: int
    explanation: str


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
