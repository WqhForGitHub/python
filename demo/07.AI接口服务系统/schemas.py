"""Pydantic 模型。"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"] = "user"
    content: str = Field(..., min_length=1)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., min_length=1, max_length=50)
    model: str | None = Field(None, description="留空使用默认模型")
    max_tokens: int | None = Field(None, ge=1, le=4096)


class ChatResponse(BaseModel):
    reply: str
    model: str
    provider: str


class TaskCreate(BaseModel):
    prompt: str = Field(..., min_length=1, description="任务提示词")


class TaskRead(BaseModel):
    task_id: str
    user_id: int
    prompt: str
    status: str
    result: str
    error: str
    model: str
    created_at: datetime
    finished_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class Message(BaseModel):
    message: str
