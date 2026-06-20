"""通用响应模型。"""
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ResponseEnvelope(BaseModel, Generic[T]):
    """统一响应包装。"""

    code: str = "OK"
    message: str = "success"
    data: T | None = None


class Message(BaseModel):
    message: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str
