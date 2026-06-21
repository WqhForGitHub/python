"""api-gateway 应用入口。

启动方式：
    uvicorn main:app --reload --port 8000

职责：
- 服务注册中心（register / heartbeat / deregister / discover）
- 反向代理：将 /api/{service}/* 请求转发到对应服务实例（负载均衡）
- 鉴权网关：受保护接口先调用 auth-service 校验 token
- 服务聚合：/api/me 串联 auth + user 两个服务

启动顺序：先启动 gateway，再启动 auth-service / user-service。
"""

import sys
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse, Response

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config  # noqa: E402
import shared.models as schemas  # noqa: E402
from shared.registry import ServiceRegistry, registry  # noqa: E402

app = FastAPI(
    title="api-gateway",
    description=(
        "微服务用户系统 - API 网关。\n\n"
        "## 架构\n"
        "- **api-gateway (8000)**：注册中心 + 反向代理 + 鉴权\n"
        "- **auth-service (8001)**：JWT 签发 / 校验\n"
        "- **user-service (8002)**：用户 CRUD\n\n"
        "## 启动顺序\n"
        "1. `uvicorn main:app --port 8000`（网关）\n"
        "2. `cd auth-service && uvicorn main:app --port 8001`\n"
        "3. `cd user-service && uvicorn main:app --port 8002`\n\n"
        "服务启动后会自动向网关注册并心跳，网关据此路由请求。"
    ),
    version="1.0.0",
)


@app.get("/", tags=["默认"], summary="欢迎页")
def root():
    return {
        "message": "欢迎使用微服务用户系统 - API 网关",
        "docs": "/docs",
        "services": "/registry/services",
    }


# ============================================================
# 服务注册中心
# ============================================================
@app.post("/registry/register", summary="注册服务")
def register_service(body: schemas.RegisterService):
    registry.register(body.name, body.host, body.port)
    return {"message": "registered", "service": body.name}


@app.post("/registry/heartbeat", summary="服务心跳")
def heartbeat(body: schemas.RegisterService):
    ok = registry.heartbeat(body.name, body.host, body.port)
    if not ok:
        # 未注册则自动注册
        registry.register(body.name, body.host, body.port)
    return {"message": "ok"}


@app.post("/registry/deregister", summary="注销服务")
def deregister(body: schemas.RegisterService):
    registry.deregister(body.name, body.host, body.port)
    return {"message": "deregistered"}


@app.get("/registry/services", summary="已注册服务列表")
def list_services():
    return registry.all_services()


# ============================================================
# 反向代理 / 路由
# ============================================================
# 路由前缀 -> 服务名映射
ROUTE_MAP = {
    "/api/auth": "auth-service",
    "/api/users": "user-service",
}

# 需要鉴权的路径前缀（除登录外）
PROTECTED_PREFIXES = {"/api/users"}


async def _proxy(service_name: str, request: Request, path_tail: str) -> Response:
    """转发请求到指定服务实例。"""
    instance = registry.discover(service_name)
    if instance is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"服务 {service_name} 暂无可用实例",
        )

    body = await request.body()
    headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.request(
                request.method,
                f"{instance.base_url}{path_tail}",
                content=body,
                headers=headers,
                params=request.query_params,
                timeout=15,
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"调用 {service_name} 失败：{e}",
            )

    excluded = {"content-encoding", "content-length", "transfer-encoding"}
    response_headers = {
        k: v for k, v in resp.headers.items() if k.lower() not in excluded
    }
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=response_headers,
        media_type=resp.headers.get("content-type"),
    )


async def _verify_token(request: Request) -> dict | None:
    """调用 auth-service 校验 token，返回用户信息或 None。"""
    auth = request.headers.get("authorization", "")
    if not auth:
        return None
    instance = registry.discover("auth-service")
    if instance is None:
        return None
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{instance.base_url}/verify",
                headers={"authorization": auth},
                timeout=10,
            )
        except httpx.RequestError:
            return None
    if resp.status_code != 200:
        return None
    data = resp.json()
    return data if data.get("valid") else None


# 通用代理入口：/api/{service-prefix}/...
@app.api_route(
    "/api/{prefix}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def gateway_proxy(prefix: str, path: str, request: Request):
    route_prefix = f"/api/{prefix}"
    service_name = ROUTE_MAP.get(route_prefix)
    if service_name is None:
        raise HTTPException(status_code=404, detail=f"未知路由前缀 {route_prefix}")

    # 鉴权
    if route_prefix in PROTECTED_PREFIXES:
        user_info = await _verify_token(request)
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未登录或 token 无效",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return await _proxy(service_name, request, f"/{prefix}/{path}")


# ============================================================
# 服务聚合示例：/api/me
# ============================================================
@app.get("/api/me", summary="聚合接口：当前登录用户信息")
async def me(request: Request):
    """串联 auth-service（校验 token）+ user-service（查用户详情）。"""
    user_info = await _verify_token(request)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或 token 无效",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = user_info["user_id"]
    instance = registry.discover("user-service")
    if instance is None:
        raise HTTPException(status_code=503, detail="user-service 不可用")
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{instance.base_url}/internal/{user_id}", timeout=10)
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="获取用户信息失败")
    return {
        "user": resp.json(),
        "verified_by": "auth-service",
        "fetched_from": "user-service",
    }
