"""Pydantic schemas for workspace scan, file list, and overview statistics."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ScanJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workspace_id: int
    status: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    files_discovered: int = 0
    files_processed: int = 0
    error: str | None = None


class WorkspaceFileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workspace_id: int
    relative_path: str
    filename: str
    extension: str
    category: str
    size_bytes: int
    modified_at: datetime
    fs_status: str
    last_scanned_at: datetime


class WorkspaceFileListResponse(BaseModel):
    items: list[WorkspaceFileResponse]
    total: int
    offset: int
    limit: int


class WorkspaceOverviewResponse(BaseModel):
    workspace_id: int
    total_files: int
    total_size_bytes: int
    files_by_category: dict[str, int]
    files_by_status: dict[str, int]
    pending_changes_count: int
    recent_files: list[WorkspaceFileResponse]
    latest_scan: ScanJobResponse | None = None


class DocumentSummaryResponse(BaseModel):
    total_supported: int
    not_started: int
    processing: int
    ready: int
    failed: int


class DocumentItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workspace_file_id: int
    filename: str
    relative_path: str
    extension: str
    category: str
    size_bytes: int
    fs_status: str
    modified_at: datetime
    extraction_status: str
    chunking_status: str
    document_status: str


class DocumentListResponse(BaseModel):
    items: list[DocumentItemResponse]
    total: int
    offset: int
    limit: int
