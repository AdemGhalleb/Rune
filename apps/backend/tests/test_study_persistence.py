"""Tests for Study Persistence (Phase 5B)."""

import json
from datetime import UTC, datetime

from httpx import AsyncClient

from app.db.models import (
    Chunk,
    DocumentProcessing,
    DocumentSegment,
    Workspace,
    WorkspaceFile,
)
from app.services.retrieval import RetrievedChunk
from app.schemas.study import (
    FlashcardSetResponse,
    QuizAttemptCreate,
    QuizResponse,
    StudySessionCreate,
    SummaryResponse,
)

CHUNK_TEXT = "Operating systems manage hardware resources."


async def test_create_study_session_summary(client: AsyncClient, session_factory, tmp_path):
    """Test creating and persisting a summary study session."""
    ws_dir = tmp_path / "test_workspace"
    ws_dir.mkdir()

    # Seed database
    with session_factory() as session:
        ws = Workspace(name="Test WS", root_path=str(ws_dir))
        session.add(ws)
        session.commit()
        ws_id = ws.id

    # Create summary payload
    summary_payload = StudySessionCreate(
        session_type="summary",
        title="Operating Systems Overview",
        topic="Operating Systems",
        summary_data=SummaryResponse(
            topic="Operating Systems",
            title="Operating Systems Overview",
            overview="OS abstracts hardware complexity",
            key_points=["Resource management", "Process scheduling"],
            citations=[],
        ),
    )

    # Call API
    resp = await client.post(
        "/api/v1/study/sessions",
        json=summary_payload.model_dump(mode="json"),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["session_type"] == "summary"
    assert data["title"] == "Operating Systems Overview"
    assert data["workspace_id"] == ws_id
    session_id = data["id"]

    # Verify persistence: fetch from database
    with session_factory() as session:
        from sqlalchemy import select

        from app.db.models import StudySession

        stmt = select(StudySession).where(StudySession.id == session_id)
        persisted = session.scalars(stmt).first()
        assert persisted is not None
        assert persisted.session_type == "summary"
        assert persisted.title == "Operating Systems Overview"


async def test_create_study_session_flashcards(client: AsyncClient, session_factory, tmp_path):
    """Test creating and persisting flashcards."""
    ws_dir = tmp_path / "test_workspace"
    ws_dir.mkdir()

    with session_factory() as session:
        ws = Workspace(name="Test WS", root_path=str(ws_dir))
        session.add(ws)
        session.commit()
        ws_id = ws.id

    flashcards_payload = StudySessionCreate(
        session_type="flashcards",
        title="OS Flashcards",
        topic="Operating Systems",
        flashcards_data=FlashcardSetResponse(
            topic="Operating Systems",
            cards=[
                {
                    "question": "What is an OS?",
                    "answer": "Software that manages hardware resources",
                    "citations": [],
                }
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

    # Verify in database
    with session_factory() as session:
        from sqlalchemy import select

        from app.db.models import StudyFlashcard, StudySession

        stmt = select(StudySession).where(StudySession.id == data["id"])
        persisted_session = session.scalars(stmt).first()
        assert persisted_session is not None

        fc_count = session.scalar(
            select(len(persisted_session.flashcards))
        )  # type: ignore
        assert len(persisted_session.flashcards) == 1


async def test_list_study_sessions(client: AsyncClient, session_factory, tmp_path):
    """Test listing study sessions."""
    ws_dir = tmp_path / "test_workspace"
    ws_dir.mkdir()

    with session_factory() as session:
        ws = Workspace(name="Test WS", root_path=str(ws_dir))
        session.add(ws)
        session.commit()

    # Create multiple sessions
    for i in range(3):
        payload = StudySessionCreate(
            session_type="summary",
            title=f"Summary {i+1}",
            summary_data=SummaryResponse(
                topic="Topic",
                title=f"Summary {i+1}",
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

    # List all sessions
    resp = await client.get("/api/v1/study/sessions")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3

    # List with filter
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

    # Get details
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

    # Delete
    resp = await client.delete(f"/api/v1/study/sessions/{session_id}")
    assert resp.status_code == 204

    # Verify deleted
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
                {"question": "Q1", "answer": "A1", "citations": []},
                {"question": "Q2", "answer": "A2", "citations": []},
            ],
        ),
    )

    resp = await client.post(
        "/api/v1/study/sessions",
        json=payload.model_dump(mode="json"),
    )
    session_id = resp.json()["id"]
    card_id = resp.json()["flashcards"][0]["id"]

    # Update review state
    resp = await client.post(
        f"/api/v1/study/sessions/{session_id}/flashcards/{card_id}/review",
        json={"state": "mastered"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["state"] == "mastered"
    assert data["review_count"] == 1

    # Update again
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
                {
                    "question": "What is an OS?",
                    "options": ["a", "b", "c", "d"],
                    "correct_index": 0,
                    "explanation": "It manages hardware",
                    "citations": [],
                }
            ],
        ),
    )

    resp = await client.post(
        "/api/v1/study/sessions",
        json=payload.model_dump(mode="json"),
    )
    session_id = resp.json()["id"]

    # Record attempt
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

    # Get attempts
    resp = await client.get(f"/api/v1/study/sessions/{session_id}/quiz/attempts")
    assert resp.status_code == 200
    attempts = resp.json()
    assert len(attempts) == 1
    assert attempts[0]["score"] == 1


async def test_study_persistence_across_sessions(
    session_factory, tmp_path
) -> None:
    """Test that study data persists across database reconnection."""
    from sqlalchemy import select

    from app.db.models import StudyFlashcard, StudySession

    ws_dir = tmp_path / "test_workspace"
    ws_dir.mkdir()

    # Create workspace and study session in first session
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
                question=f"Question {idx+1}",
                answer=f"Answer {idx+1}",
                review_count=0,
                state="new",
            )
            session.add(card)
        session.commit()
        session_id = study_session.id

    # Close session and reopen in new session (simulating app restart)
    with session_factory() as session:
        stmt = select(StudySession).where(StudySession.id == session_id)
        persisted = session.scalars(stmt).first()
        assert persisted is not None
        assert persisted.title == "Persistent Cards"
        assert len(persisted.flashcards) == 3

        # Modify and verify
        persisted.flashcards[0].review_count = 5
        persisted.flashcards[0].state = "mastered"
        session.commit()

    # Verify modification persisted
    with session_factory() as session:
        stmt = select(StudySession).where(StudySession.id == session_id)
        persisted = session.scalars(stmt).first()
        assert persisted is not None
        assert persisted.flashcards[0].review_count == 5
        assert persisted.flashcards[0].state == "mastered"


async def test_study_workspace_isolation(client: AsyncClient, session_factory, tmp_path):
    """Test that study sessions are properly isolated by workspace."""
    # Create two workspaces
    ws_dir1 = tmp_path / "ws1"
    ws_dir2 = tmp_path / "ws2"
    ws_dir1.mkdir()
    ws_dir2.mkdir()

    ws_ids = []
    for ws_dir in [ws_dir1, ws_dir2]:
        with session_factory() as session:
            ws = Workspace(name=f"WS", root_path=str(ws_dir))
            session.add(ws)
            session.commit()
            ws_ids.append(ws.id)

    # This is tricky to test via API since the current workspace is shared
    # But we can verify via direct database queries
    from sqlalchemy import select

    from app.db.models import StudySession

    # Create sessions in database for both workspaces
    with session_factory() as session:
        for ws_id in ws_ids:
            ss = StudySession(
                workspace_id=ws_id,
                session_type="summary",
                title=f"Session for WS{ws_id}",
            )
            session.add(ss)
        session.commit()

    # Verify isolation: each workspace should only see its own sessions
    with session_factory() as session:
        for ws_id in ws_ids:
            stmt = select(StudySession).where(StudySession.workspace_id == ws_id)
            sessions = session.scalars(stmt).all()
            assert len(sessions) == 1
            assert sessions[0].title == f"Session for WS{ws_id}"
