"""Study Persistence Service (Phase 5B).

Handles persistent storage, retrieval, reviews, and attempt logging for study sessions.
"""

import json
import logging
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db.models import (
    FlashcardState,
    StudyFlashcard,
    StudyFlashcardCitation,
    StudyQuizAttempt,
    StudyQuizQuestion,
    StudyQuizQuestionCitation,
    StudySession,
    StudySessionCitation,
    StudySessionType,
)
from app.schemas.study import (
    ExplanationResponse,
    FlashcardItemPersisted,
    FlashcardReviewUpdate,
    QuizAttemptCreate,
    QuizAttemptResponse,
    QuizQuestionPersisted,
    StudyCitation,
    StudySessionCreate,
    StudySessionDetail,
    StudySessionSummary,
    SummaryResponse,
)

logger = logging.getLogger(__name__)


class StudyPersistenceService:
    """Service managing database persistence for study sessions, cards, quizzes, and attempts."""

    def __init__(self, session: Session, workspace_id: int) -> None:
        self.session = session
        self.workspace_id = workspace_id

    def create_session(self, payload: StudySessionCreate) -> StudySessionDetail:
        """Create a new persistent study session."""
        content_json: str | None = None

        if payload.session_type == StudySessionType.SUMMARY.value and payload.summary_data:
            content_json = payload.summary_data.model_dump_json()
        elif (
            payload.session_type == StudySessionType.EXPLANATION.value and payload.explanation_data
        ):
            content_json = payload.explanation_data.model_dump_json()

        study_session = StudySession(
            workspace_id=self.workspace_id,
            session_type=payload.session_type,
            title=payload.title,
            topic=payload.topic,
            workspace_file_id=payload.workspace_file_id,
            content_json=content_json,
        )
        self.session.add(study_session)
        self.session.flush()

        # Citations for top-level session (Summary & Explanation)
        top_citations = []
        if payload.summary_data:
            top_citations = payload.summary_data.citations
        elif payload.explanation_data:
            top_citations = payload.explanation_data.citations

        for rank, cite in enumerate(top_citations, start=1):
            sc = StudySessionCitation(
                session_id=study_session.id,
                chunk_id=cite.chunk_id,
                workspace_file_id=cite.workspace_file_id,
                snippet=cite.snippet,
                relevance_score=cite.relevance_score,
                rank=rank,
            )
            self.session.add(sc)

        # Flashcards
        if payload.flashcards_data:
            for idx, card in enumerate(payload.flashcards_data.cards):
                fc = StudyFlashcard(
                    session_id=study_session.id,
                    card_index=idx,
                    question=card.question,
                    answer=card.answer,
                    review_count=0,
                    state=FlashcardState.NEW.value,
                )
                self.session.add(fc)
                self.session.flush()

                for cite in card.citations:
                    fcc = StudyFlashcardCitation(
                        flashcard_id=fc.id,
                        chunk_id=cite.chunk_id,
                        workspace_file_id=cite.workspace_file_id,
                        snippet=cite.snippet,
                        relevance_score=cite.relevance_score,
                    )
                    self.session.add(fcc)

        # Quiz questions
        if payload.quiz_data:
            for idx, q in enumerate(payload.quiz_data.questions):
                qq = StudyQuizQuestion(
                    session_id=study_session.id,
                    question_index=idx,
                    question=q.question,
                    options_json=json.dumps(q.options),
                    correct_index=q.correct_index,
                    explanation=q.explanation,
                )
                self.session.add(qq)
                self.session.flush()

                for cite in q.citations:
                    qqc = StudyQuizQuestionCitation(
                        quiz_question_id=qq.id,
                        chunk_id=cite.chunk_id,
                        workspace_file_id=cite.workspace_file_id,
                        snippet=cite.snippet,
                        relevance_score=cite.relevance_score,
                    )
                    self.session.add(qqc)

        self.session.commit()
        detail = self.get_session(study_session.id)
        if not detail:
            raise RuntimeError("Failed to retrieve created study session")
        return detail

    def list_sessions(
        self,
        session_type: str | None = None,
        workspace_file_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[StudySessionSummary]:
        """List persistent study sessions for the workspace."""
        stmt = (
            select(StudySession)
            .where(StudySession.workspace_id == self.workspace_id)
            .order_by(StudySession.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        if session_type:
            stmt = stmt.where(StudySession.session_type == session_type)
        if workspace_file_id is not None:
            stmt = stmt.where(StudySession.workspace_file_id == workspace_file_id)

        sessions = self.session.scalars(stmt).all()
        results: list[StudySessionSummary] = []

        for s in sessions:
            item_count = 0
            if s.session_type == StudySessionType.FLASHCARDS.value:
                item_count = (
                    self.session.scalar(
                        select(func.count(StudyFlashcard.id)).where(
                            StudyFlashcard.session_id == s.id
                        )
                    )
                    or 0
                )
            elif s.session_type == StudySessionType.QUIZ.value:
                item_count = (
                    self.session.scalar(
                        select(func.count(StudyQuizQuestion.id)).where(
                            StudyQuizQuestion.session_id == s.id
                        )
                    )
                    or 0
                )

            attempt_count = 0
            best_score: int | None = None
            if s.session_type == StudySessionType.QUIZ.value:
                attempt_count = (
                    self.session.scalar(
                        select(func.count(StudyQuizAttempt.id)).where(
                            StudyQuizAttempt.session_id == s.id
                        )
                    )
                    or 0
                )
                if attempt_count > 0:
                    best_score = self.session.scalar(
                        select(func.max(StudyQuizAttempt.score)).where(
                            StudyQuizAttempt.session_id == s.id
                        )
                    )

            results.append(
                StudySessionSummary(
                    id=s.id,
                    workspace_id=s.workspace_id,
                    session_type=s.session_type,
                    title=s.title,
                    topic=s.topic,
                    workspace_file_id=s.workspace_file_id,
                    created_at=s.created_at,
                    updated_at=s.updated_at,
                    item_count=item_count,
                    attempt_count=attempt_count,
                    best_score=best_score,
                )
            )

        return results

    def get_session(self, session_id: int) -> StudySessionDetail | None:
        """Get full details of a persistent study session."""
        stmt = (
            select(StudySession)
            .where(
                StudySession.id == session_id,
                StudySession.workspace_id == self.workspace_id,
            )
            .options(
                selectinload(StudySession.citations).selectinload(
                    StudySessionCitation.workspace_file
                ),
                selectinload(StudySession.flashcards)
                .selectinload(StudyFlashcard.citations)
                .selectinload(StudyFlashcardCitation.workspace_file),
                selectinload(StudySession.quiz_questions)
                .selectinload(StudyQuizQuestion.citations)
                .selectinload(StudyQuizQuestionCitation.workspace_file),
                selectinload(StudySession.quiz_attempts),
            )
        )
        s = self.session.scalars(stmt).first()
        if not s:
            return None

        # Build citations
        citations = [
            StudyCitation(
                chunk_id=c.chunk_id,
                workspace_file_id=c.workspace_file_id,
                filename=c.workspace_file.filename if c.workspace_file else "unknown",
                snippet=c.snippet or "",
                relevance_score=c.relevance_score,
            )
            for c in s.citations
        ]

        summary_data: SummaryResponse | None = None
        if s.session_type == StudySessionType.SUMMARY.value and s.content_json:
            try:
                raw = json.loads(s.content_json)
                summary_data = SummaryResponse(
                    topic=raw.get("topic", s.topic or s.title),
                    title=raw.get("title", s.title),
                    overview=raw.get("overview", ""),
                    key_points=raw.get("key_points", []),
                    citations=citations,
                )
            except Exception as err:
                logger.warning(
                    "Failed to deserialize summary content_json for session %s: %s",
                    s.id,
                    err,
                )

        explanation_data: ExplanationResponse | None = None
        if s.session_type == StudySessionType.EXPLANATION.value and s.content_json:
            try:
                raw = json.loads(s.content_json)
                explanation_data = ExplanationResponse(
                    topic=raw.get("topic", s.topic or s.title),
                    explanation=raw.get("explanation", ""),
                    key_takeaways=raw.get("key_takeaways", []),
                    citations=citations,
                )
            except Exception as err:
                logger.warning(
                    "Failed to deserialize explanation content_json for session %s: %s",
                    s.id,
                    err,
                )

        flashcards = [
            FlashcardItemPersisted(
                id=fc.id,
                card_index=fc.card_index,
                question=fc.question,
                answer=fc.answer,
                review_count=fc.review_count,
                state=fc.state,
                last_reviewed_at=fc.last_reviewed_at,
                citations=[
                    StudyCitation(
                        chunk_id=fcc.chunk_id,
                        workspace_file_id=fcc.workspace_file_id,
                        filename=fcc.workspace_file.filename if fcc.workspace_file else "unknown",
                        snippet=fcc.snippet or "",
                        relevance_score=fcc.relevance_score,
                    )
                    for fcc in fc.citations
                ],
            )
            for fc in s.flashcards
        ]

        quiz_questions: list[QuizQuestionPersisted] = []
        for qq in s.quiz_questions:
            options: list[str] = []
            try:
                options = json.loads(qq.options_json)
            except Exception:
                options = []
            quiz_questions.append(
                QuizQuestionPersisted(
                    id=qq.id,
                    question_index=qq.question_index,
                    question=qq.question,
                    options=options,
                    correct_index=qq.correct_index,
                    explanation=qq.explanation,
                    citations=[
                        StudyCitation(
                            chunk_id=qqc.chunk_id,
                            workspace_file_id=qqc.workspace_file_id,
                            filename=qqc.workspace_file.filename
                            if qqc.workspace_file
                            else "unknown",
                            snippet=qqc.snippet or "",
                            relevance_score=qqc.relevance_score,
                        )
                        for qqc in qq.citations
                    ],
                )
            )

        quiz_attempts: list[QuizAttemptResponse] = []
        for qa in s.quiz_attempts:
            answers: dict[str, int] = {}
            try:
                answers = json.loads(qa.answers_json)
            except Exception:
                answers = {}
            quiz_attempts.append(
                QuizAttemptResponse(
                    id=qa.id,
                    session_id=qa.session_id,
                    score=qa.score,
                    total_questions=qa.total_questions,
                    answers=answers,
                    completed_at=qa.completed_at,
                    created_at=qa.created_at,
                )
            )

        return StudySessionDetail(
            id=s.id,
            workspace_id=s.workspace_id,
            session_type=s.session_type,
            title=s.title,
            topic=s.topic,
            workspace_file_id=s.workspace_file_id,
            created_at=s.created_at,
            updated_at=s.updated_at,
            summary_data=summary_data,
            flashcards=flashcards,
            quiz_questions=quiz_questions,
            quiz_attempts=quiz_attempts,
            explanation_data=explanation_data,
            citations=citations,
        )

    def delete_session(self, session_id: int) -> bool:
        """Delete a persistent study session by id."""
        stmt = select(StudySession).where(
            StudySession.id == session_id,
            StudySession.workspace_id == self.workspace_id,
        )
        s = self.session.scalars(stmt).first()
        if not s:
            return False
        self.session.delete(s)
        self.session.commit()
        return True

    def update_flashcard_review(
        self, session_id: int, card_id: int, review: FlashcardReviewUpdate
    ) -> FlashcardItemPersisted:
        """Update flashcard review state."""
        stmt = (
            select(StudyFlashcard)
            .join(StudySession)
            .where(
                StudyFlashcard.id == card_id,
                StudyFlashcard.session_id == session_id,
                StudySession.workspace_id == self.workspace_id,
            )
            .options(
                selectinload(StudyFlashcard.citations).selectinload(
                    StudyFlashcardCitation.workspace_file
                )
            )
        )
        card = self.session.scalars(stmt).first()
        if not card:
            raise KeyError(f"Flashcard {card_id} not found in session {session_id}")

        card.review_count += 1
        card.state = review.state
        card.last_reviewed_at = datetime.now(UTC)
        self.session.commit()

        return FlashcardItemPersisted(
            id=card.id,
            card_index=card.card_index,
            question=card.question,
            answer=card.answer,
            review_count=card.review_count,
            state=card.state,
            last_reviewed_at=card.last_reviewed_at,
            citations=[
                StudyCitation(
                    chunk_id=fcc.chunk_id,
                    workspace_file_id=fcc.workspace_file_id,
                    filename=fcc.workspace_file.filename if fcc.workspace_file else "unknown",
                    snippet=fcc.snippet or "",
                    relevance_score=fcc.relevance_score,
                )
                for fcc in card.citations
            ],
        )

    def record_quiz_attempt(
        self, session_id: int, attempt: QuizAttemptCreate
    ) -> QuizAttemptResponse:
        """Record a completed quiz attempt."""
        stmt = select(StudySession).where(
            StudySession.id == session_id,
            StudySession.workspace_id == self.workspace_id,
            StudySession.session_type == StudySessionType.QUIZ.value,
        )
        session = self.session.scalars(stmt).first()
        if not session:
            raise KeyError(f"Quiz session {session_id} not found")

        now = datetime.now(UTC)
        qa = StudyQuizAttempt(
            session_id=session_id,
            score=attempt.score,
            total_questions=attempt.total_questions,
            answers_json=json.dumps(attempt.answers),
            completed_at=now,
            created_at=now,
        )
        self.session.add(qa)
        self.session.commit()

        return QuizAttemptResponse(
            id=qa.id,
            session_id=qa.session_id,
            score=qa.score,
            total_questions=qa.total_questions,
            answers=attempt.answers,
            completed_at=qa.completed_at,
            created_at=qa.created_at,
        )

    def get_quiz_attempts(self, session_id: int) -> list[QuizAttemptResponse]:
        """Get history of quiz attempts for a session."""
        stmt = (
            select(StudyQuizAttempt)
            .join(StudySession)
            .where(
                StudyQuizAttempt.session_id == session_id,
                StudySession.workspace_id == self.workspace_id,
            )
            .order_by(StudyQuizAttempt.created_at.desc())
        )
        attempts = self.session.scalars(stmt).all()
        results: list[QuizAttemptResponse] = []
        for qa in attempts:
            answers: dict[str, int] = {}
            try:
                answers = json.loads(qa.answers_json)
            except Exception:
                answers = {}
            results.append(
                QuizAttemptResponse(
                    id=qa.id,
                    session_id=qa.session_id,
                    score=qa.score,
                    total_questions=qa.total_questions,
                    answers=answers,
                    completed_at=qa.completed_at,
                    created_at=qa.created_at,
                )
            )
        return results
