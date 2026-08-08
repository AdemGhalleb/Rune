"""Workspace selection API endpoints."""

from collections.abc import Generator

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session, sessionmaker

from app.db.database import get_session
from app.schemas.workspace import WorkspaceResponse, WorkspaceSetRequest, WorkspaceUpdateRequest
from app.services.workspace import WorkspaceService

router = APIRouter(prefix="/workspace", tags=["workspace"])


def get_db_session(request: Request) -> Generator[Session, None, None]:
    session_factory: sessionmaker[Session] = request.app.state.session_factory
    yield from get_session(session_factory)


@router.get("", response_model=WorkspaceResponse | None)
def get_workspace(session: Session = Depends(get_db_session)) -> WorkspaceResponse | None:
    return WorkspaceService().get_current(session)


@router.put("", response_model=WorkspaceResponse, status_code=status.HTTP_200_OK)
def set_workspace(
    payload: WorkspaceSetRequest, session: Session = Depends(get_db_session)
) -> WorkspaceResponse:
    return WorkspaceService().set_current(session, root_path=payload.root_path, name=payload.name)


@router.patch("", response_model=WorkspaceResponse)
def update_workspace(
    payload: WorkspaceUpdateRequest, session: Session = Depends(get_db_session)
) -> WorkspaceResponse:
    return WorkspaceService().update_current(
        session, root_path=payload.root_path, name=payload.name
    )


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def remove_workspace(session: Session = Depends(get_db_session)) -> Response:
    WorkspaceService().remove_current(session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
