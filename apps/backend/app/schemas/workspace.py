"""Workspace API schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WorkspaceSetRequest(BaseModel):
    root_path: str = Field(min_length=1, max_length=2048)
    name: str | None = Field(default=None, min_length=1, max_length=255)


class WorkspaceUpdateRequest(BaseModel):
    root_path: str | None = Field(default=None, min_length=1, max_length=2048)
    name: str | None = Field(default=None, min_length=1, max_length=255)


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    root_path: str
    name: str
    created_at: datetime
    updated_at: datetime
