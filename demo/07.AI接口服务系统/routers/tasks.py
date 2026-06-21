"""异步任务队列接口。

提交任务后立即返回 task_id，后台 worker 异步处理，通过 GET 查询结果。
"""

import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import crud.task
import queue
import schemas
from database import get_db
from deps import get_user_id, rate_limit

router = APIRouter(prefix="/tasks", tags=["异步任务队列"])


@router.post(
    "/",
    response_model=schemas.TaskRead,
    status_code=status.HTTP_201_CREATED,
    summary="提交异步任务",
)
def create_task(
    body: schemas.TaskCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(rate_limit),
):
    task = crud.task.create_task(db, user_id, body.prompt)
    queue.task_queue.enqueue(task.task_id)
    return task


@router.get(
    "/",
    response_model=list[schemas.TaskRead],
    summary="我的任务列表",
)
def list_tasks(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id),
):
    return crud.task.list_tasks_by_user(db, user_id, skip, limit)


@router.get(
    "/{task_id}",
    response_model=schemas.TaskRead,
    summary="查询任务状态与结果",
)
def get_task(task_id: str, db: Session = Depends(get_db)):
    task = crud.task.get_task_by_id(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.get(
    "/{task_id}/wait",
    response_model=schemas.TaskRead,
    summary="轮询等待任务完成（最多 30 秒）",
)
def wait_task(task_id: str, db: Session = Depends(get_db)):
    """简化版轮询：在服务端阻塞循环查询，最多 30 秒。"""
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        task = crud.task.get_task_by_id(db, task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="任务不存在")
        if task.status in ("succeeded", "failed"):
            return task
        time.sleep(0.5)
    return crud.task.get_task_by_id(db, task_id)
