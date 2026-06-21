"""服务间 HTTP 调用客户端 + 服务注册 / 心跳辅助。

- 注册：服务启动时向网关 POST /registry/register
- 心跳：后台任务定期 POST /registry/heartbeat
- 注销：服务关闭时 POST /registry/deregister（best-effort）
- 调用：discover 后用 httpx 转发
"""

import asyncio

import httpx


async def register_to_gateway(
    gateway_url: str, name: str, host: str, port: int
) -> None:
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{gateway_url}/registry/register",
            json={"name": name, "host": host, "port": port},
            timeout=5,
        )


async def heartbeat_loop(
    gateway_url: str, name: str, host: str, port: int, interval: float = 5.0
) -> None:
    """持续向网关发送心跳。"""
    async with httpx.AsyncClient() as client:
        while True:
            try:
                await client.post(
                    f"{gateway_url}/registry/heartbeat",
                    json={"name": name, "host": host, "port": port},
                    timeout=3,
                )
            except Exception:  # noqa: BLE001  网关不可用时不影响服务自身
                pass
            await asyncio.sleep(interval)


async def deregister_from_gateway(
    gateway_url: str, name: str, host: str, port: int
) -> None:
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{gateway_url}/registry/deregister",
                json={"name": name, "host": host, "port": port},
                timeout=3,
            )
    except Exception:  # noqa: BLE001
        pass


async def call_service(
    base_url: str, method: str, path: str, **kwargs
) -> httpx.Response:
    """调用下游服务。"""
    async with httpx.AsyncClient() as client:
        return await client.request(method, f"{base_url}{path}", timeout=10, **kwargs)
