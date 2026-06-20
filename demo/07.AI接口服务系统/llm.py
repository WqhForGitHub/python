"""LLM 客户端封装。

支持两种 provider：
1. mock：本地模拟回复，无需任何 API key，Demo 默认
2. openai：调用 OpenAI / 兼容接口（需安装 openai 库并配置 key）

二者实现统一接口 chat(messages, model, max_tokens) -> (reply, model, provider)。
"""
import asyncio
import time

import config


def _mock_reply(messages: list[dict]) -> str:
    """根据消息生成模拟回复。"""
    last_user = next(
        (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
    )
    return (
        f"[MOCK LLM 回复]\n"
        f"已收到你的提问（{len(last_user)} 字）：\n"
        f"> {last_user[:200]}\n\n"
        f"这是一条由本地 mock 生成的占位回复。配置 OPENAI_API_KEY 并设置 "
        f"LLM_PROVIDER=openai 即可调用真实模型。"
    )


async def chat_openai(
    messages: list[dict], model: str, max_tokens: int
) -> tuple[str, str, str]:
    """调用 OpenAI 兼容接口。"""
    from openai import AsyncOpenAI  # type: ignore

    client = AsyncOpenAI(
        api_key=config.OPENAI_API_KEY,
        base_url=config.OPENAI_BASE_URL or None,
    )
    resp = await client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
    )
    reply = resp.choices[0].message.content or ""
    return reply, model, "openai"


async def chat(
    messages: list[dict],
    model: str | None = None,
    max_tokens: int | None = None,
) -> tuple[str, str, str]:
    """统一入口。返回 (reply, model, provider)。"""
    model = model or config.OPENAI_MODEL
    max_tokens = max_tokens or config.LLM_MAX_TOKENS

    if config.LLM_PROVIDER == "openai" and config.OPENAI_API_KEY:
        try:
            return await chat_openai(messages, model, max_tokens)
        except Exception as e:  # noqa: BLE001
            # 调用失败时降级为 mock，保证 Demo 可用
            return (
                f"[LLM 调用失败，降级 mock]\n错误：{e}\n\n{_mock_reply(messages)}",
                model,
                "mock(fallback)",
            )

    # mock 模式：模拟网络延迟
    await asyncio.sleep(config.MOCK_LATENCY)
    return _mock_reply(messages), model, "mock"


def chat_sync(
    messages: list[dict],
    model: str | None = None,
    max_tokens: int | None = None,
) -> tuple[str, str, str]:
    """同步包装（供后台 worker 线程使用）。"""
    return asyncio.run(chat(messages, model, max_tokens))
