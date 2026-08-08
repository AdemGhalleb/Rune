"""Business logic for selecting and managing Rune's workspace."""

from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import Workspace
from app.db.repositories import WorkspaceRepository


class WorkspaceService:
    def __init__(self, repository: WorkspaceRepository | None = None) -> None:
        self.repository = repository or WorkspaceRepository()

    def get_current(self, session: Session) -> Workspace | None:
        return self.repository.get_current(session)

    def set_current(self, session: Session, *, root_path: str, name: str | None) -> Workspace:
        normalized_path = self._validate_directory(root_path)
        clean_name = name.strip() if name and name.strip() else None
        resolved_name = clean_name or Path(normalized_path).name or normalized_path
        workspace = self.repository.get_current(session)
        if workspace is None:
            return self.repository.create(session, root_path=normalized_path, name=resolved_name)
        return self.repository.update(
            session, workspace, root_path=normalized_path, name=resolved_name
        )

    def update_current(
        self, session: Session, *, root_path: str | None, name: str | None
    ) -> Workspace:
        workspace = self._get_required(session)
        normalized_path = (
            self._validate_directory(root_path) if root_path is not None else workspace.root_path
        )
        clean_name = name.strip() if name and name.strip() else None
        resolved_name = clean_name if clean_name is not None else workspace.name
        return self.repository.update(
            session, workspace, root_path=normalized_path, name=resolved_name
        )

    def remove_current(self, session: Session) -> None:
        self.repository.delete(session, self._get_required(session))

    def _get_required(self, session: Session) -> Workspace:
        workspace = self.repository.get_current(session)
        if workspace is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No workspace is selected"
            )
        return workspace

    @staticmethod
    def _validate_directory(root_path: str) -> str:
        clean_path = root_path.strip()
        if not clean_path:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Workspace path must be an existing directory",
            )
        path = Path(clean_path).expanduser()
        if not path.is_dir():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Workspace path must be an existing directory",
            )
        return str(path.resolve())
