"""日志查询与性能统计接口。"""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

import crud.log
import metrics
import schemas
from database import get_db

router = APIRouter(tags=["日志与监控"])


@router.get(
    "/logs",
    summary="请求日志列表（支持筛选）",
)
def list_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    method: str | None = Query(None, description="按 HTTP 方法筛选"),
    status_code: int | None = Query(None, description="按状态码筛选"),
    path: str | None = Query(None, description="路径模糊匹配"),
    since_minutes: int | None = Query(None, description="最近 N 分钟"),
    db: Session = Depends(get_db),
):
    items, total = crud.log.list_logs(
        db, skip=skip, limit=limit, method=method,
        status_code=status_code, path=path, since_minutes=since_minutes,
    )
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get(
    "/logs/{request_id}",
    response_model=schemas.RequestLogRead,
    summary="按 request_id 查询日志详情",
)
def get_log(request_id: str, db: Session = Depends(get_db)):
    log = crud.log.get_log_by_id(db, request_id)
    if log is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="日志不存在")
    return log


@router.get(
    "/stats/summary",
    response_model=schemas.StatsSummary,
    summary="性能汇总（最近 N 分钟）",
)
def stats_summary(since_minutes: int = Query(60, ge=1), db: Session = Depends(get_db)):
    return crud.log.get_summary(db, since_minutes=since_minutes)


@router.get(
    "/stats/paths",
    response_model=list[schemas.PathStat],
    summary="按接口路径聚合的性能统计",
)
def stats_paths(
    since_minutes: int = Query(60, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return crud.log.get_path_stats(db, since_minutes=since_minutes, limit=limit)


@router.get(
    "/metrics",
    response_class=PlainTextResponse,
    summary="Prometheus 指标端点",
    tags=["Prometheus"],
)
def prometheus_metrics():
    """供 Prometheus / Grafana 抓取的指标端点。"""
    return PlainTextResponse(
        metrics.render_metrics(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
