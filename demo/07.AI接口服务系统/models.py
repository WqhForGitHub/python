"""SQLAlchemy ORM 模型。

AITask 记录异步任务的状态与结果。
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from database import Base


class AITask(Base):
    __tablename__ = "ai_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(64), unique=True, index=True, nullable=False)  # UUID
    user_id = Column(Integer, nullable=False, index=True)
    prompt = Column(Text, nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    # pending / running / succeeded / failed
    result = Column(Text, default="", nullable=False)
    error = Column(Text, default="", nullable=False)
    retries = Column(Integer, default=0, nullable=False)
    model = Column(String(64), default="", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    finished_at = Column(DateTime, nullable=True)
