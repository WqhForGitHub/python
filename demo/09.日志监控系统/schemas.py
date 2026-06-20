"""Pydantic 模型。"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class RequestLogRead(BaseModel):
    id: int
    request_id: str
    method: str
    path: str
    status_code: int
    duration_ms: int
    client_ip: str
    user_agent: str
    user_id: int | None
    error: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StatsSummary(BaseModel):
    total: int
    success: int          # 2xx
    client_error: int     # 4xx
    server_error: int     # 5xx
    avg_duration_ms: float
    p95_duration_ms: float
    max_duration_ms: int


class PathStat(BaseModel):
    path: str
    method: str
    count: int
    avg_duration_ms: float
    max_duration_ms: int
    error_count: int


class Message(BaseModel):
    message: str
