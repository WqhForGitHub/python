"""认证相关 Schema。"""
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, pattern=r"^[A-Za-z0-9_]+$", examples=["alice"])
    email: EmailStr = Field(..., examples=["alice@example.com"])
    password: str = Field(..., min_length=6, max_length=32, examples=["Secret123"])

    @field_validator("password")
    @classmethod
    def password_rule(cls, v: str) -> str:
        if not any(c.isalpha() for c in v) or not any(c.isdigit() for c in v):
            raise ValueError("密码必须同时包含字母和数字")
        return v


class UserLogin(BaseModel):
    username: str
    password: str
