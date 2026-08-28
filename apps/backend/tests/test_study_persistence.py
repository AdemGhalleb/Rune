"""Tests for Study Persistence (Phase 5B)."""

from datetime import UTC, datetime

from httpx import AsyncClient
from sqlalchemy import inspect, select

from app.core.config import Settings
from app.db.database import create_database_engine, run_migrations
from app.db.models import (
    Chunk,
    DocumentProcessing,
    DocumentSegment,
    ExtractionStatus,
    FlashcardState,
    SegmentType,
    StudyFlashcard,
    StudyFlashcardCitation,
    StudySession,
    Workspace,
    WorkspaceFile,
)
from app.schemas.study import (
    ExplanationResponse,
    FlashcardItem,
    FlashcardReviewUpdate,
    FlashcardSetResponse,
    QuizAttemptCreate,
    QuizQuestion,
    QuizResponse,
    StudyCitation,
    StudySessionCreate,
    SummaryResponse,
)
from app.services.study_persistence import StudyPersistenceService


def _seed_workspace_with_file_and_chunk(session, ws: Workspace) -> tuple[WorkspaceFile, Chunk]:
    wf = WorkspaceFile(
        workspace_id=ws.id,
        relative_path="docs/lecture1.pdf",
        filename="lecture1.pdf",
        extension=".pdf",
        category="document",
        size_bytes=1024,
        modified_at=datetime.now(UTC),
        fs_status="clean",
    )
    session.add(wf)
    session.flush()

    dp = DocumentProcessing(
        workspace_file_id=wf.id,
        extraction_status=ExtractionStatus.EXTRACTED.value,
    )
    session.add(dp)
    session.flush()

    seg = DocumentSegment(
        document_processing_id=dp.id,
        segment_index=0,
        segment_type=SegmentType.PDF_PAGE.value,
        text="Sample page text",
        char_count=16,
    )
    session.add(seg)
    session.flush()

    chunk = Chunk(
        document_processing_id=dp.id,
        segment_id=seg.id,
        chunk_index=0,
        text="Operating systems manage hardware resources.",
        char_start=0,
        char_end=44,
        char_count=44,
        content_hash="abc123hash",
    )
    session.add(chunk)
    session.flush()
    return wf, chunk


async def test_create_study_session_summary(client: AsyncClient, session_factory, tmp_path):
    """Test creating and persisting a summary study session."""
    ws_dir = tmp_path / "test_workspace"
    ws_dir.mkdir()

    with session_factory() as session:
        ws = Workspace(name="Test WS", root_path=str(ws_dir))
        session.add(ws)
        session.commit()
        ws_id = ws.id
        wf, chunk = _seed_workspace_with_file_and_chunk(session, ws)
        wf_id = wf.id
        chunk_id = chunk.id
        session.commit()

    summary_payload = StudySessionCreate(
        session_type="summary",
        title="Operating Systems Overview",
        topic="Operating Systems",
        workspace_file_id=wf_id,
        summary_data=SummaryResponse(
            topic="Operating Systems",
            title="Operating Systems Overview",
            overview="OS abstracts hardware complexity",
            key_points=["Resource management", "Process scheduling"],
            citations=[
                StudyCitation(
                    chunk_id=chunk_id,
                    workspace_file_id=wf_id,
                    filename="lecture1.pdf",
                    snippet="Operating systems manage hardware resources.",
                    relevance_score=0.95,
                )
            ],
        ),
    )

    resp = await client.post(
        "/api/v1/study/sessions",
        json=summary_payload.model_dump(mode="json"),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["session_type"] == "summary"
    assert data["title"] == "Operating Systems Overview"
    assert data["workspace_id"] == ws_id
    assert len(data["citations"]) == 1
    assert data["citations"][0]["chunk_id"] == chunk_id
    session_id = data["id"]

    with session_factory() as session:
        stmt = select(StudySession).where(StudySession.id == session_id)
        persisted = session.scalars(stmt).first()
        assert persisted is not None
        assert persisted.session_type == "summary"
        assert persisted.title == "Operating Systems Overview"
        assert len(persisted.citations) == 1


async def test_create_study_session_flashcards(client: AsyncClient, session_factory, tmp_path):
    """Test creating and persisting flashcards with citations."""
    ws_dir = tmp_path / "test_workspace"
    ws_dir.mkdir()

    with session_factory() as session:
        ws = Workspace(name="Test WS", root_path=str(ws_dir))
        session.add(ws)
        session.commit()
        wf, chunk = _seed_workspace_with_file_and_chunk(session, ws)
        wf_id = wf.id
        chunk_id = chunk.id
        session.commit()

    flashcards_payload = StudySessionCreate(
        session_type="flashcards",
        title="OS Flashcards",
        topic="Operating Systems",
        flashcards_data=FlashcardSetResponse(
            topic="Operating Systems",
            cards=[
                FlashcardItem(
                    question="What is an OS?",
                    answer="Software that manages hardware resources",
                    citations=[
                        StudyCitation(
                            chunk_id=chunk_id,
                            workspace_file_id=wf_id,
                            filename="lecture1.pdf",
                            snippet="Operating systems manage hardware resources.",
                            relevance_score=0.92,
                        )
                    ],
                )
            ],
        ),
    )

    resp = await client.post(
        "/api/v1/study/sessions",
        json=flashcards_payload.model_dump(mode="json"),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["session_type"] == "flashcards"
    assert len(data["flashcards"]) == 1
    assert data["flashcards"][0]["question"] == "What is an OS?"
    assert data["flashcards"][0]["state"] == "new"
    assert data["flashcards"][0]["review_count"] == 0
    assert len(data["flashcards"][0]["citations"]) == 1
    assert data["flashcards"][0]["citations"][0]["chunk_id"] == chunk_id

    with session_factory() as session:
        stmt = select(StudySession).where(StudySession.id == data["id"])
        persisted_session = session.scalars(stmt).first()
        assert persisted_session is not None
        assert len(persisted_session.flashcards) == 1
        assert len(persisted_session.flashcards[0].citations) == 1


async def test_create_study_session_explanation(client: AsyncClient, session_factory, tmp_path):
    """Test creating and persisting an explanation study session."""
    ws_dir = tmp_path / "test_workspace"
    ws_dir.mkdir()

    with session_factory() as session:
        ws = Workspace(name="Test WS", root_path=str(ws_dir))
        session.add(ws)
        session.commit()
        wf, chunk = _seed_workspace_with_file_and_chunk(session, ws)
        wf_id = wf.id
        chunk_id = chunk.id
        session.commit()

    explanation_payload = StudySessionCreate(
        session_type="explanation",
        title="Virtual Memory Deep Dive",
        topic="Virtual Memory",
        explanation_data=ExplanationResponse(
            topic="Virtual Memory",
            explanation="Virtual memory provides memory abstraction per process.",
            key_takeaways=["Isolation", "Paging", "Swap space"],
            citations=[
                StudyCitation(
                    chunk_id=chunk_id,
                    workspace_file_id=wf_id,
                    filename="lecture1.pdf",
                    snippet="Operating systems manage hardware resources.",
                    relevance_score=0.88,
                )
            ],
        ),
    )

    resp = await client.post(
        "/api/v1/study/sessions",
        json=explanation_payload.model_dump(mode="json"),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["session_type"] == "explanation"
    assert data["explanation_data"]["topic"] == "Virtual Memory"
    assert len(data["citations"]) == 1


async def test_list_study_sessions(client: AsyncClient, session_factory, tmp_path):
    """Test listing study sessions with filtering."""
    ws_dir = tmp_path / "test_workspace"
    ws_dir.mkdir()

    with session_factory() as session:
        ws = Workspace(name="Test WS", root_path=str(ws_dir))
        session.add(ws)
        session.commit()

    for i in range(3):
        payload = StudySessionCreate(
            session_type="summary",
            title=f"Summary {i + 1}",
            summary_data=SummaryResponse(
                topic="Topic",
                title=f"Summary {i + 1}",
                overview="Overview",
                key_points=[],
                citations=[],
            ),
        )
        resp = await client.post(
            "/api/v1/study/sessions",
            json=payload.model_dump(mode="json"),
        )
        assert resp.status_code == 201

    resp = await client.get("/api/v1/study/sessions")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3

    resp = await client.get("/api/v1/study/sessions?session_type=summary")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    assert all(s["session_type"] == "summary" for s in data)


async def test_get_study_session_detail(client: AsyncClient, session_factory, tmp_path):
    """Test retrieving full session details."""
    ws_dir = tmp_path / "test_workspace"
    ws_dir.mkdir()

    with session_factory() as session:
        ws = Workspace(name="Test WS", root_path=str(ws_dir))
        session.add(ws)
        session.commit()

    payload = StudySessionCreate(
        session_type="summary",
        title="Test Summary",
        summary_data=SummaryResponse(
            topic="Algorithms",
            title="Test Summary",
            overview="Big O notation simplifies complexity analysis",
            key_points=["Linear", "Quadratic", "Exponential"],
            citations=[],
        ),
    )

    resp = await client.post(
        "/api/v1/study/sessions",
        json=payload.model_dump(mode="json"),
    )
    session_id = resp.json()["id"]

    resp = await client.get(f"/api/v1/study/sessions/{session_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == session_id
    assert data["summary_data"]["key_points"] == ["Linear", "Quadratic", "Exponential"]


async def test_delete_study_session(client: AsyncClient, session_factory, tmp_path):
    """Test deleting a study session."""
    ws_dir = tmp_path / "test_workspace"
    ws_dir.mkdir()

    with session_factory() as session:
        ws = Workspace(name="Test WS", root_path=str(ws_dir))
        session.add(ws)
        session.commit()

    payload = StudySessionCreate(
        session_type="summary",
        title="Temp Session",
        summary_data=SummaryResponse(
            topic="Test",
            title="Temp",
            overview="Temporary",
            key_points=[],
            citations=[],
        ),
    )

    resp = await client.post(
        "/api/v1/study/sessions",
        json=payload.model_dump(mode="json"),
    )
    session_id = resp.json()["id"]

    resp = await client.delete(f"/api/v1/study/sessions/{session_id}")
    assert resp.status_code == 204

    resp = await client.get(f"/api/v1/study/sessions/{session_id}")
    assert resp.status_code == 404


async def test_update_flashcard_review_state(client: AsyncClient, session_factory, tmp_path):
    """Test updating flashcard review state."""
    ws_dir = tmp_path / "test_workspace"
    ws_dir.mkdir()

    with session_factory() as session:
        ws = Workspace(name="Test WS", root_path=str(ws_dir))
        session.add(ws)
        session.commit()

    payload = StudySessionCreate(
        session_type="flashcards",
        title="Cards",
        flashcards_data=FlashcardSetResponse(
            topic="Test",
            cards=[
                FlashcardItem(question="Q1", answer="A1", citations=[]),
                FlashcardItem(question="Q2", answer="A2", citations=[]),
            ],
        ),
    )

    resp = await client.post(
        "/api/v1/study/sessions",
        json=payload.model_dump(mode="json"),
    )
    session_id = resp.json()["id"]
    card_id = resp.json()["flashcards"][0]["id"]

    resp = await client.post(
        f"/api/v1/study/sessions/{session_id}/flashcards/{card_id}/review",
        json={"state": "mastered"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["state"] == "mastered"
    assert data["review_count"] == 1

    resp = await client.post(
        f"/api/v1/study/sessions/{session_id}/flashcards/{card_id}/review",
        json={"state": "shaky"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["state"] == "shaky"
    assert data["review_count"] == 2


async def test_record_quiz_attempt(client: AsyncClient, session_factory, tmp_path):
    """Test recording quiz attempts."""
    ws_dir = tmp_path / "test_workspace"
    ws_dir.mkdir()

    with session_factory() as session:
        ws = Workspace(name="Test WS", root_path=str(ws_dir))
        session.add(ws)
        session.commit()

    payload = StudySessionCreate(
        session_type="quiz",
        title="Quiz",
        quiz_data=QuizResponse(
            topic="OS",
            questions=[
                QuizQuestion(
                    question="What is an OS?",
                    options=["a", "b", "c", "d"],
                    correct_index=0,
                    explanation="It manages hardware",
                    citations=[],
                )
            ],
        ),
    )

    resp = await client.post(
        "/api/v1/study/sessions",
        json=payload.model_dump(mode="json"),
    )
    session_id = resp.json()["id"]

    attempt_payload = QuizAttemptCreate(score=1, total_questions=1, answers={"0": 0})
    resp = await client.post(
        f"/api/v1/study/sessions/{session_id}/quiz/attempt",
        json=attempt_payload.model_dump(mode="json"),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["score"] == 1
    assert data["total_questions"] == 1
    assert data["answers"] == {"0": 0}

    resp = await client.get(f"/api/v1/study/sessions/{session_id}/quiz/attempts")
    assert resp.status_code == 200
    attempts = resp.json()
    assert len(attempts) == 1
    assert attempts[0]["score"] == 1


async def test_study_persistence_across_sessions(session_factory, tmp_path) -> None:
    """Test that study data persists across database reconnection."""
    ws_dir = tmp_path / "test_workspace"
    ws_dir.mkdir()

    with session_factory() as session:
        ws = Workspace(name="Persistent WS", root_path=str(ws_dir))
        session.add(ws)
        session.flush()

        study_session = StudySession(
            workspace_id=ws.id,
            session_type="flashcards",
            title="Persistent Cards",
            topic="Persistence Testing",
        )
        session.add(study_session)
        session.flush()

        for idx in range(3):
            card = StudyFlashcard(
                session_id=study_session.id,
                card_index=idx,
                question=f"Question {idx + 1}",
                answer=f"Answer {idx + 1}",
                review_count=0,
                state=FlashcardState.NEW.value,
            )
            session.add(card)
        session.commit()
        session_id = study_session.id

    with session_factory() as session:
        stmt = select(StudySession).where(StudySession.id == session_id)
        persisted = session.scalars(stmt).first()
        assert persisted is not None
        assert persisted.title == "Persistent Cards"
        assert len(persisted.flashcards) == 3

        persisted.flashcards[0].review_count = 5
        persisted.flashcards[0].state = FlashcardState.MASTERED.value
        session.commit()

    with session_factory() as session:
        stmt = select(StudySession).where(StudySession.id == session_id)
        persisted = session.scalars(stmt).first()
        assert persisted is not None
        assert persisted.flashcards[0].review_count == 5
        assert persisted.flashcards[0].state == FlashcardState.MASTERED.value


async def test_study_workspace_isolation_service(session_factory, tmp_path):
    """Test strict workspace isolation at the service level."""
    ws_dir1 = tmp_path / "ws1"
    ws_dir2 = tmp_path / "ws2"
    ws_dir1.mkdir()
    ws_dir2.mkdir()

    with session_factory() as session:
        ws1 = Workspace(name="WS1", root_path=str(ws_dir1))
        ws2 = Workspace(name="WS2", root_path=str(ws_dir2))
        session.add_all([ws1, ws2])
        session.commit()
        ws1_id, ws2_id = ws1.id, ws2.id

        service1 = StudyPersistenceService(session=session, workspace_id=ws1_id)
        service2 = StudyPersistenceService(session=session, workspace_id=ws2_id)

        s1 = service1.create_session(
            StudySessionCreate(
                session_type="flashcards",
                title="WS1 Cards",
                flashcards_data=FlashcardSetResponse(
                    topic="WS1 Topic",
                    cards=[FlashcardItem(question="Q1", answer="A1", citations=[])],
                ),
            )
        )

        assert service1.get_session(s1.id) is not None
        assert service2.get_session(s1.id) is None

        ws2_sessions = service2.list_sessions()
        assert len(ws2_sessions) == 0

        assert service2.delete_session(s1.id) is False

        try:
            service2.update_flashcard_review(
                session_id=s1.id,
                card_id=s1.flashcards[0].id,
                review=FlashcardReviewUpdate(state="mastered"),
            )
            raise AssertionError("Should have raised KeyError")
        except KeyError:
            pass


async def test_study_workspace_isolation_api(client: AsyncClient, session_factory, tmp_path):
    """Test workspace isolation through HTTP API endpoints."""
    ws_dir1 = tmp_path / "ws1"
    ws_dir2 = tmp_path / "ws2"
    ws_dir1.mkdir()
    ws_dir2.mkdir()

    with session_factory() as session:
        ws1 = Workspace(name="WS 1", root_path=str(ws_dir1))
        ws2 = Workspace(name="WS 2", root_path=str(ws_dir2))
        session.add_all([ws1, ws2])
        session.commit()
        ws2_id = ws2.id

        # Seed a session directly for ws2 (other workspace)
        service2 = StudyPersistenceService(session=session, workspace_id=ws2_id)
        s2 = service2.create_session(
            StudySessionCreate(
                session_type="summary",
                title="WS2 Private Summary",
                summary_data=SummaryResponse(
                    topic="WS2",
                    title="WS2 Private Summary",
                    overview="Private to WS2",
                    key_points=[],
                    citations=[],
                ),
            )
        )
        s2_id = s2.id

    # Active workspace for client is WS1 (lowest id)
    # Trying to fetch WS2's session via API must return 404
    resp = await client.get(f"/api/v1/study/sessions/{s2_id}")
    assert resp.status_code == 404

    # Listing sessions under WS1 should not show WS2's session
    resp = await client.get("/api/v1/study/sessions")
    assert resp.status_code == 200
    listed_ids = [s["id"] for s in resp.json()]
    assert s2_id not in listed_ids

    # Deleting WS2's session through WS1 active workspace must return 404
    resp = await client.delete(f"/api/v1/study/sessions/{s2_id}")
    assert resp.status_code == 404


async def test_fresh_database_migration_and_schema(tmp_path):
    """Test that all Phase 5B migrations apply cleanly to a fresh database."""
    fresh_settings = Settings(data_dir=tmp_path / "fresh_data")
    run_migrations(fresh_settings)
    engine = create_database_engine(fresh_settings)

    try:
        insp = inspect(engine)
        tables = insp.get_table_names()
        expected_tables = [
            "study_sessions",
            "study_flashcards",
            "study_quiz_questions",
            "study_quiz_attempts",
            "study_session_citations",
            "study_flashcard_citations",
            "study_quiz_question_citations",
        ]
        for t in expected_tables:
            assert t in tables, f"Expected table {t} to exist in fresh migrated database"

        session_cols = {c["name"] for c in insp.get_columns("study_sessions")}
        assert {"id", "workspace_id", "session_type", "title", "content_json"}.issubset(
            session_cols
        )
    finally:
        engine.dispose()


async def test_cascade_deletions(session_factory, tmp_path):
    """Test cascade deletion behavior for study sessions and relationships."""
    ws_dir = tmp_path / "test_workspace"
    ws_dir.mkdir()

    with session_factory() as session:
        ws = Workspace(name="Cascade WS", root_path=str(ws_dir))
        session.add(ws)
        session.flush()

        wf, chunk = _seed_workspace_with_file_and_chunk(session, ws)

        ss = StudySession(
            workspace_id=ws.id,
            session_type="flashcards",
            title="Cascade Cards",
            workspace_file_id=wf.id,
        )
        session.add(ss)
        session.flush()

        card = StudyFlashcard(
            session_id=ss.id,
            card_index=0,
            question="Q?",
            answer="A!",
        )
        session.add(card)
        session.flush()

        cite = StudyFlashcardCitation(
            flashcard_id=card.id,
            chunk_id=chunk.id,
            workspace_file_id=wf.id,
        )
        session.add(cite)
        session.commit()

        ss_id = ss.id
        card_id = card.id
        cite_id = cite.id
        ws_id = ws.id

    with session_factory() as session:
        ws_obj = session.get(Workspace, ws_id)
        assert ws_obj is not None
        session.delete(ws_obj)
        session.commit()

    with session_factory() as session:
        assert session.get(StudySession, ss_id) is None
        assert session.get(StudyFlashcard, card_id) is None
        assert session.get(StudyFlashcardCitation, cite_id) is None
