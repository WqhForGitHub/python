"""SQLAlchemy ORM 模型。

RequestLog 记录每次 HTTP 请求的追踪信息。
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from database import Base


class RequestLog(Base):
    __tablename__ = "request_logs"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(64), unique=True, index=True, nullable=False)
    method = Column(String(10), index=True, nullable=False)
    path = Column(String(255), index=True, nullable=False)
    status_code = Column(Integer, index=True, nullable=False)
    duration_ms = Column(Integer, nullable=False)
    client_ip = Column(String(64), default="", nullable=False)
    user_agent = Column(String(255), default="", nullable=False)
    user_id = Column(Integer, nullable=True, index=True)  # 可选，来自鉴权
    # error 字段：非 2xx 时记录异常信息
    error = Column(Text, default="", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
