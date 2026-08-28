"""Schemas for grounded study generation (Phase 5A)."""

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
