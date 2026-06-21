"""Pydantic 模型 (Schema)。"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=50, examples=["alice"])


class UserRead(BaseModel):
    id: int
    username: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FileRead(BaseModel):
    id: int
    filename: str
    stored_key: str
    content_type: str
    size: int
    checksum: str
    visibility: str
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FileUpdate(BaseModel):
    visibility: Optional[Literal["public", "private", "shared"]] = None


class ShareCreate(BaseModel):
    shared_with_user_id: int = Field(..., gt=0)


class Message(BaseModel):
    message: str
