"""微服务间共享的 Pydantic 模型。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, examples=["alice"])
    email: str = Field(..., examples=["alice@example.com"])
    password: str = Field(..., min_length=6, examples=["Secret123"])


class UserRead(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str


class VerifyResponse(BaseModel):
    valid: bool
    user_id: int | None = None
    username: str | None = None


class RegisterService(BaseModel):
    name: str
    host: str
    port: int


class Message(BaseModel):
    message: str
