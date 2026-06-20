"""示例业务接口：用于产生日志 / 触发不同状态码 / 模拟慢请求。

访问这些接口会产生 RequestLog 与 Prometheus 指标，便于演示监控效果。
"""
import asyncio
import random

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/demo", tags=["示例业务"])


@router.get("/ok", summary="正常请求（200）")
def ok():
    return {"message": "ok", "tip": "查看 /logs 或 /metrics 中的记录"}


@router.get("/slow", summary="慢请求（约 1.5 秒）")
async def slow():
    await asyncio.sleep(1.5)
    return {"message": "slow done"}


@router.get("/random", summary="随机耗时（0~2 秒）")
async def random_latency():
    t = random.uniform(0, 2)
    await asyncio.sleep(t)
    return {"message": "done", "duration": round(t, 3)}


@router.get("/error", summary="触发 500 错误")
def error():
    raise HTTPException(status_code=500, detail="故意触发的服务器错误")


@router.get("/notfound", summary="触发 404")
def notfound():
    raise HTTPException(status_code=404, detail="故意触发的未找到")


@router.get("/echo/{item_id}", summary="带路径参数（演示路径归一化）")
def echo(item_id: int):
    return {"item_id": item_id}
