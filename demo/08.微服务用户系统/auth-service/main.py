"""auth-service 应用入口。

启动方式：
    uvicorn main:app --reload --port 8001 --host 0.0.0.0

职责：
- 登录签发 JWT（调用 user-service 校验凭据）
- Token 校验接口（供网关 / 其他服务调用）
- 启动时向网关注册，后台心跳保活
"""
import asyncio
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, status
from jose import JWTError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config  # noqa: E402
import security  # noqa: E402
import shared.client as service_client  # noqa: E402
import shared.models as schemas  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    await service_client.register_to_gateway(
        config.GATEWAY_URL, config.SERVICE_NAME, config.SERVICE_HOST, config.SERVICE_PORT
    )
    hb = asyncio.create_task(
        service_client.heartbeat_loop(
            config.GATEWAY_URL, config.SERVICE_NAME, config.SERVICE_HOST, config.SERVICE_PORT
        )
    )
    yield
    hb.cancel()
    await service_client.deregister_from_gateway(
        config.GATEWAY_URL, config.SERVICE_NAME, config.SERVICE_HOST, config.SERVICE_PORT
    )


app = FastAPI(
    title="auth-service",
    description="微服务用户系统 - 认证服务（JWT 签发 / 校验）",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["健康检查"], summary="健康检查")
def health():
    return {"service": config.SERVICE_NAME, "status": "ok"}


@app.post("/login", response_model=schemas.TokenResponse, summary="登录")
async def login(body: schemas.LoginRequest):
    """登录：远程调用 user-service 校验凭据，签发 JWT。"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{config.USER_SERVICE_URL}/internal/verify",
                json=body.model_dump(),
                timeout=10,
            )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"user-service 不可用：{e}",
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    user = resp.json()
    token = security.create_access_token(user["id"], user["username"])
    return schemas.TokenResponse(
        access_token=token,
        user_id=user["id"],
        username=user["username"],
    )


@app.get("/verify", response_model=schemas.VerifyResponse, summary="校验 Token")
def verify_token(authorization: str = ""):
    """供网关调用的 token 校验接口。"""
    if not authorization.lower().startswith("bearer "):
        return schemas.VerifyResponse(valid=False)
    token = authorization.split(" ", 1)[1]
    try:
        payload = security.decode_token(token)
        return schemas.VerifyResponse(
            valid=True,
            user_id=int(payload.get("sub")),
            username=payload.get("username"),
        )
    except (JWTError, ValueError, TypeError):
        return schemas.VerifyResponse(valid=False)
