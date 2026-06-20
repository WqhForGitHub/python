"""AI 任务 CRUD 操作。"""
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

import config
import models


def get_task(db: Session, task_id: int) -> models.AITask | None:
    return db.query(models.AITask).filter(models.AITask.id == task_id).first()


def get_task_by_id(db: Session, task_id: str) -> models.AITask | None:
    return db.query(models.AITask).filter(models.AITask.task_id == task_id).first()


def list_tasks_by_user(
    db: Session, user_id: int, skip: int = 0, limit: int = 50
) -> list[models.AITask]:
    return (
        db.query(models.AITask)
        .filter(models.AITask.user_id == user_id)
        .order_by(models.AITask.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_task(db: Session, user_id: int, prompt: str) -> models.AITask:
    task = models.AITask(
        task_id=uuid.uuid4().hex,
        user_id=user_id,
        prompt=prompt,
        status="pending",
        model=config.OPENAI_MODEL,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def mark_running(db: Session, task: models.AITask) -> None:
    task.status = "running"
    db.commit()


def mark_succeeded(
    db: Session, task: models.AITask, result: str, model: str
) -> None:
    task.status = "succeeded"
    task.result = result
    task.model = model
    task.finished_at = datetime.utcnow()
    db.commit()


def mark_retrying(db: Session, task: models.AITask, error: str) -> None:
    task.status = "pending"
    task.error = error
    db.commit()


def mark_failed(db: Session, task: models.AITask, error: str) -> None:
    task.status = "failed"
    task.error = error
    task.finished_at = datetime.utcnow()
    db.commit()
