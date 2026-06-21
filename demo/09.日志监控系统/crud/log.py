"""日志查询 + 性能统计 CRUD。"""

from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

import models


def get_log_by_id(db: Session, request_id: str) -> models.RequestLog | None:
    return (
        db.query(models.RequestLog)
        .filter(models.RequestLog.request_id == request_id)
        .first()
    )


def list_logs(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    method: str | None = None,
    status_code: int | None = None,
    path: str | None = None,
    since_minutes: int | None = None,
) -> tuple[list[models.RequestLog], int]:
    stmt = db.query(models.RequestLog)
    if method:
        stmt = stmt.filter(models.RequestLog.method == method)
    if status_code:
        stmt = stmt.filter(models.RequestLog.status_code == status_code)
    if path:
        stmt = stmt.filter(models.RequestLog.path.like(f"%{path}%"))
    if since_minutes:
        stmt = stmt.filter(
            models.RequestLog.created_at
            >= datetime.utcnow() - timedelta(minutes=since_minutes)
        )
    total = stmt.count()
    items = stmt.order_by(models.RequestLog.id.desc()).offset(skip).limit(limit).all()
    return items, total


def get_summary(db: Session, since_minutes: int = 60) -> dict:
    """性能汇总：总数 / 成功 / 4xx / 5xx / 平均 / P95 / 最大耗时。"""
    since = datetime.utcnow() - timedelta(minutes=since_minutes)
    base = db.query(models.RequestLog).filter(models.RequestLog.created_at >= since)
    total = base.count()
    if total == 0:
        return {
            "total": 0,
            "success": 0,
            "client_error": 0,
            "server_error": 0,
            "avg_duration_ms": 0.0,
            "p95_duration_ms": 0.0,
            "max_duration_ms": 0,
        }
    success = base.filter(models.RequestLog.status_code < 400).count()
    client_error = base.filter(
        models.RequestLog.status_code >= 400, models.RequestLog.status_code < 500
    ).count()
    server_error = base.filter(models.RequestLog.status_code >= 500).count()

    avg = (
        db.query(func.avg(models.RequestLog.duration_ms))
        .filter(models.RequestLog.created_at >= since)
        .scalar()
        or 0.0
    )
    max_dur = (
        db.query(func.max(models.RequestLog.duration_ms))
        .filter(models.RequestLog.created_at >= since)
        .scalar()
        or 0
    )

    # P95：取排序后第 95% 位置的记录
    all_durations = (
        db.query(models.RequestLog.duration_ms)
        .filter(models.RequestLog.created_at >= since)
        .order_by(models.RequestLog.duration_ms)
        .all()
    )
    if all_durations:
        idx = int(len(all_durations) * 0.95)
        idx = min(idx, len(all_durations) - 1)
        p95 = all_durations[idx][0]
    else:
        p95 = 0

    return {
        "total": total,
        "success": success,
        "client_error": client_error,
        "server_error": server_error,
        "avg_duration_ms": round(float(avg), 2),
        "p95_duration_ms": float(p95),
        "max_duration_ms": int(max_dur),
    }


def get_path_stats(db: Session, since_minutes: int = 60, limit: int = 20) -> list[dict]:
    """按 path + method 聚合的接口性能统计。"""
    since = datetime.utcnow() - timedelta(minutes=since_minutes)
    rows = (
        db.query(
            models.RequestLog.path,
            models.RequestLog.method,
            func.count(models.RequestLog.id).label("count"),
            func.avg(models.RequestLog.duration_ms).label("avg"),
            func.max(models.RequestLog.duration_ms).label("max"),
        )
        .filter(models.RequestLog.created_at >= since)
        .group_by(models.RequestLog.path, models.RequestLog.method)
        .order_by(func.count(models.RequestLog.id).desc())
        .limit(limit)
        .all()
    )
    result = []
    for path, method, count, avg, max_dur in rows:
        error_count = (
            db.query(func.count(models.RequestLog.id))
            .filter(
                models.RequestLog.path == path,
                models.RequestLog.method == method,
                models.RequestLog.status_code >= 400,
                models.RequestLog.created_at >= since,
            )
            .scalar()
            or 0
        )
        result.append(
            {
                "path": path,
                "method": method,
                "count": count,
                "avg_duration_ms": round(float(avg), 2),
                "max_duration_ms": int(max_dur),
                "error_count": error_count,
            }
        )
    return result
