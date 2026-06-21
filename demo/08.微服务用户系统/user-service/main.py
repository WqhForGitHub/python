"""user-service 应用入口。

启动方式：
    uvicorn main:app --reload --port 8002 --host 0.0.0.0

职责：
- 用户 CRUD
- 凭据校验接口（供 auth-service 调用）
- 启动时向网关注册，后台心跳保活
"""

import asyncio
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

# 将项目根目录加入 sys.path 以便 import shared
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config  # noqa: E402
import crud  # noqa: E402
import models  # noqa: E402
import shared.client as service_client  # noqa: E402
import shared.models as schemas  # noqa: E402
from database import SessionLocal, engine, get_db  # noqa: E402

models.Base.metadata.create_all(bind=engine)
_seed()


def _seed() -> None:
    db = SessionLocal()
    try:
        if db.query(models.User).count() == 0:
            db.add(
                models.User(
                    username="alice",
                    email="alice@example.com",
                    password_hash=models.hash_password("Alice123456"),
                )
            )
            db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动：注册 + 心跳
    await service_client.register_to_gateway(
        config.GATEWAY_URL,
        config.SERVICE_NAME,
        config.SERVICE_HOST,
        config.SERVICE_PORT,
    )
    hb = asyncio.create_task(
        service_client.heartbeat_loop(
            config.GATEWAY_URL,
            config.SERVICE_NAME,
            config.SERVICE_HOST,
            config.SERVICE_PORT,
        )
    )
    yield
    hb.cancel()
    await service_client.deregister_from_gateway(
        config.GATEWAY_URL,
        config.SERVICE_NAME,
        config.SERVICE_HOST,
        config.SERVICE_PORT,
    )


app = FastAPI(
    title="user-service",
    description="微服务用户系统 - 用户服务（CRUD + 凭据校验）",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["健康检查"], summary="健康检查")
def health():
    return {"service": config.SERVICE_NAME, "status": "ok"}


# 供 auth-service 远程调用的凭据校验接口（内部接口）
@app.post(
    "/internal/verify", response_model=schemas.UserRead, summary="凭据校验（内部）"
)
def verify_credentials(body: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = crud.verify_credentials(db, body.username, body.password)
    if user is None:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return user


@app.get(
    "/internal/{user_id}", response_model=schemas.UserRead, summary="按 ID 查询（内部）"
)
def internal_get_user(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@app.get("/users", response_model=list[schemas.UserRead], summary="用户列表")
def list_users(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return crud.list_users(db, skip, limit)


@app.get("/users/{user_id}", response_model=schemas.UserRead, summary="用户详情")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@app.post(
    "/users",
    response_model=schemas.UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="创建用户",
)
def create_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_username(db, user_in.username):
        raise HTTPException(status_code=400, detail="用户名已存在")
    if crud.get_user_by_email(db, user_in.email):
        raise HTTPException(status_code=400, detail="邮箱已被注册")
    return crud.create_user(db, user_in)
