"""FastAPI 应用入口。

启动方式：
    uvicorn main:app --reload

电商购物车系统 Demo：
- 商品查询（Redis 缓存）
- 购物车（Redis 存储）
- 下单接口（扣库存 / 生成订单）
"""
from fastapi import FastAPI

import cache
import models
from database import engine
from routers import cart, orders, products

# 启动时建表 + 写入示例商品
models.Base.metadata.create_all(bind=engine)
_seed()


def _seed() -> None:
    """写入示例商品（幂等）。"""
    from database import SessionLocal

    db = SessionLocal()
    try:
        if db.query(models.Product).count() == 0:
            samples = [
                models.Product(name="iPhone 15", description="苹果手机", price=6999, stock=50, image_url=""),
                models.Product(name="MacBook Pro", description="苹果笔记本", price=14999, stock=20, image_url=""),
                models.Product(name="AirPods Pro", description="苹果耳机", price=1999, stock=100, image_url=""),
            ]
            db.add_all(samples)
            db.commit()
    finally:
        db.close()


app = FastAPI(
    title="电商购物车系统",
    description=(
        "基于 FastAPI 的电商购物车系统 Demo。\n\n"
        "## 功能特性\n"
        "- **商品查询**：列表 / 详情，详情带 Redis 缓存\n"
        "- **购物车**：基于 Redis Hash 存储，支持增删改查\n"
        "- **下单接口**：从购物车生成订单，扣减库存，订单明细快照\n"
        "- **缓存降级**：无 Redis 时自动降级为内存缓存\n\n"
        f"## 当前缓存模式\n`{'Redis' if cache.is_redis_available() else '内存降级'}`\n\n"
        "## 用户标识\n购物车接口通过请求头 `X-User-Id` 标识用户。"
    ),
    version="1.0.0",
)


@app.get("/", tags=["默认"], summary="欢迎页")
def root():
    return {
        "message": "欢迎使用电商购物车系统",
        "docs": "/docs",
        "redoc": "/redoc",
        "cache_mode": "redis" if cache.is_redis_available() else "memory",
    }


app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)
