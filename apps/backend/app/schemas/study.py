"""Schemas for grounded study generation and persistence (Phase 5A & 5B)."""

from datetime import datetime

from pydantic import BaseModel, Field


class StudyCitation(BaseModel):
    """Citation metadata tracing generated study material back to source chunks."""

    chunk_id: int
    workspace_file_id: int
    filename: str
    snippet: str
    relevance_score: float | None = None


# --- Summary ---


class SummaryRequest(BaseModel):
    topic: str | None = Field(default=None, description="Optional topic or concept to summarize")
    workspace_file_id: int | None = Field(
        default=None, description="Optional specific workspace document to summarize"
    )


class SummaryResponse(BaseModel):
    topic: str
    title: str
    overview: str
    key_points: list[str]
    citations: list[StudyCitation] = Field(default_factory=list)


# --- Flashcards ---


class FlashcardsRequest(BaseModel):
    topic: str | None = Field(
        default=None, description="Optional topic or concept for the flashcards"
    )
    workspace_file_id: int | None = Field(
        default=None, description="Optional specific document to generate cards from"
    )
    count: int = Field(default=5, ge=1, le=20, description="Number of flashcards to generate")


class FlashcardItem(BaseModel):
    question: str
    answer: str
    citations: list[StudyCitation] = Field(default_factory=list)


class FlashcardSetResponse(BaseModel):
    topic: str
    cards: list[FlashcardItem]


# --- Quiz ---


class QuizRequest(BaseModel):
    topic: str | None = Field(default=None, description="Optional topic or concept for the quiz")
    workspace_file_id: int | None = Field(
        default=None, description="Optional specific document to generate quiz from"
    )
    count: int = Field(default=5, ge=1, le=20, description="Number of quiz questions to generate")


class QuizQuestion(BaseModel):
    question: str
    options: list[str]
    correct_index: int
    explanation: str
    citations: list[StudyCitation] = Field(default_factory=list)


class QuizResponse(BaseModel):
    topic: str
    questions: list[QuizQuestion]


# --- Explanation ---


class ExplanationRequest(BaseModel):
    topic: str = Field(..., min_length=1, description="Topic or concept to explain")
    workspace_file_id: int | None = Field(
        default=None, description="Optional specific document to draw explanation from"
    )


class ExplanationResponse(BaseModel):
    topic: str
    explanation: str
    key_takeaways: list[str]
    citations: list[StudyCitation] = Field(default_factory=list)


# --- Phase 5B: Study Persistence Schemas ---


class FlashcardItemPersisted(BaseModel):
    id: int
    card_index: int
    question: str
    answer: str
    review_count: int
    state: str
    last_reviewed_at: datetime | None = None
    citations: list[StudyCitation] = Field(default_factory=list)


class QuizQuestionPersisted(BaseModel):
    id: int
    question_index: int
    question: str
    options: list[str]
    correct_index: int
    explanation: str
    citations: list[StudyCitation] = Field(default_factory=list)


class QuizAttemptCreate(BaseModel):
    score: int = Field(..., ge=0)
    total_questions: int = Field(..., ge=1)
    answers: dict[str, int] = Field(default_factory=dict)


class QuizAttemptResponse(BaseModel):
    id: int
    session_id: int
    score: int
    total_questions: int
    answers: dict[str, int] = Field(default_factory=dict)
    completed_at: datetime
    created_at: datetime


class FlashcardReviewUpdate(BaseModel):
    state: str = Field(..., description="Review state: 'learning', 'shaky', 'mastered'")


class StudySessionCreate(BaseModel):
    session_type: str = Field(
        ..., description="Session type: 'summary', 'flashcards', 'quiz', 'explanation'"
    )
    title: str = Field(..., min_length=1, max_length=255)
    topic: str | None = None
    workspace_file_id: int | None = None
    summary_data: SummaryResponse | None = None
    flashcards_data: FlashcardSetResponse | None = None
    quiz_data: QuizResponse | None = None
    explanation_data: ExplanationResponse | None = None


class StudySessionSummary(BaseModel):
    id: int
    workspace_id: int
    session_type: str
    title: str
    topic: str | None
    workspace_file_id: int | None
    created_at: datetime
    updated_at: datetime
    item_count: int = 0
    attempt_count: int = 0
    best_score: int | None = None


class StudySessionDetail(BaseModel):
    id: int
    workspace_id: int
    session_type: str
    title: str
    topic: str | None
    workspace_file_id: int | None
    created_at: datetime
    updated_at: datetime
    summary_data: SummaryResponse | None = None
    flashcards: list[FlashcardItemPersisted] = Field(default_factory=list)
    quiz_questions: list[QuizQuestionPersisted] = Field(default_factory=list)
    quiz_attempts: list[QuizAttemptResponse] = Field(default_factory=list)
    explanation_data: ExplanationResponse | None = None
    citations: list[StudyCitation] = Field(default_factory=list)
