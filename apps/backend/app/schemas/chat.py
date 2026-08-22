from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=255)


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str | None
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    conversation_id: int
    role: str
    content: str
    status: str
    model_used: str | None
    error: str | None
    created_at: datetime
    updated_at: datetime


class ConversationDetail(ConversationResponse):
    messages: list[MessageResponse]


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=10000)


class SourceResponse(BaseModel):
    id: int
    chunk_id: int
    workspace_file_id: int
    filename: str
    rank: int
    relevance_score: float | None
