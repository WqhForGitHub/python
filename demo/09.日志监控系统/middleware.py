"""请求日志 + 链路追踪中间件。

功能：
1. 为每个请求生成 / 透传 request_id（X-Request-ID）
2. 记录 method / path / status / duration / client_ip / user_agent
3. 慢请求打 WARN 日志
4. 同步写入 Prometheus 指标
5. 异步落库 RequestLog（使用独立 Session，避免污染请求 Session）

request_id 可用于跨服务链路追踪：下游服务透传同一 X-Request-ID。
"""
import logging
import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

import config
import metrics
from database import SessionLocal
from models import RequestLog

logger = logging.getLogger("request")
logging.basicConfig(level=logging.INFO)


def _get_or_create_request_id(request: Request) -> str:
    rid = request.headers.get(config.REQUEST_ID_HEADER)
    if not rid:
        rid = uuid.uuid4().hex
    return rid


def _save_log(log: RequestLog) -> None:
    """独立 Session 写入日志，避免影响业务事务。"""
    db = SessionLocal()
    try:
        db.add(log)
        db.commit()
    except Exception as e:  # noqa: BLE001  日志写入失败不应影响主流程
        logger.error(f"写入请求日志失败：{e}")
    finally:
        db.close()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 跳过指标端点本身，避免自引用
        if request.url.path == "/metrics":
            return await call_next(request)

        request_id = _get_or_create_request_id(request)
        # 放入 request.state 供业务读取
        request.state.request_id = request_id

        method = request.method
        # 归一化路径（数字 ID 替换为 {id}）便于指标聚合
        raw_path = request.url.path
        path = _normalize_path(raw_path)

        metrics.REQUEST_IN_PROGRESS.labels(method=method).inc()
        start = time.monotonic()

        error_msg = ""
        status_code = 500
        try:
            response: Response = await call_next(request)
            status_code = response.status_code
            # 回写 request_id 到响应头，便于客户端关联
            response.headers[config.REQUEST_ID_HEADER] = request_id
            return response
        except Exception as e:  # noqa: BLE001
            error_msg = repr(e)
            raise
        finally:
            duration_ms = int((time.monotonic() - start) * 1000)
            metrics.REQUEST_IN_PROGRESS.labels(method=method).dec()
            metrics.record_request(method, path, status_code, duration_ms)

            # 慢请求告警
            if duration_ms / 1000 >= config.SLOW_REQUEST_THRESHOLD:
                logger.warning(
                    f"[SLOW] {request_id} {method} {raw_path} "
                    f"-> {status_code} ({duration_ms}ms)"
                )
            else:
                logger.info(
                    f"{request_id} {method} {raw_path} "
                    f"-> {status_code} ({duration_ms}ms)"
                )

            # 落库（同步，单独 Session）
            _save_log(
                RequestLog(
                    request_id=request_id,
                    method=method,
                    path=raw_path,
                    status_code=status_code,
                    duration_ms=duration_ms,
                    client_ip=request.client.host if request.client else "",
                    user_agent=request.headers.get("user-agent", "")[:255],
                    user_id=getattr(request.state, "user_id", None),
                    error=error_msg,
                )
            )


def _normalize_path(path: str) -> str:
    """将路径中的数字 ID 替换为 {id}，避免指标基数爆炸。"""
    parts = []
    for seg in path.split("/"):
        if seg.isdigit():
            parts.append("{id}")
        else:
            parts.append(seg)
    return "/".join(parts)
