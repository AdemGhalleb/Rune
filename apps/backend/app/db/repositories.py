"""Data-access operations for SQLAlchemy models."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Workspace


class WorkspaceRepository:
    """Persistence operations for the application's one selected workspace."""

    def get_current(self, session: Session) -> Workspace | None:
        return session.scalar(select(Workspace).order_by(Workspace.id).limit(1))

    def create(self, session: Session, *, root_path: str, name: str) -> Workspace:
        workspace = Workspace(root_path=root_path, name=name)
        session.add(workspace)
        session.commit()
        session.refresh(workspace)
        return workspace

    def update(
        self, session: Session, workspace: Workspace, *, root_path: str, name: str
    ) -> Workspace:
        workspace.root_path = root_path
        workspace.name = name
        session.commit()
        session.refresh(workspace)
        return workspace

    def delete(self, session: Session, workspace: Workspace) -> None:
        session.delete(workspace)
        session.commit()
