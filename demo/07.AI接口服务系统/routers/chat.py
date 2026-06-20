"""同步聊天接口（实时返回 LLM 回复，带限流）。"""
from fastapi import APIRouter, Depends

import limiter
import llm
import schemas
from deps import get_user_id, rate_limit

router = APIRouter(prefix="/chat", tags=["同步聊天"])


@router.post(
    "/completions",
    response_model=schemas.ChatResponse,
    summary="同步聊天（实时返回）",
)
async def chat_completions(
    body: schemas.ChatRequest,
    user_id: int = Depends(rate_limit),
):
    messages = [{"role": m.role, "content": m.content} for m in body.messages]
    reply, model, provider = await llm.chat(
        messages, model=body.model, max_tokens=body.max_tokens
    )
    return schemas.ChatResponse(
        reply=reply, model=f"{model} ({provider})", provider=provider
    )


@router.get(
    "/rate-limit",
    summary="查询当前用户限流状态",
)
def rate_limit_status(user_id: int = Depends(get_user_id)):
    return {"user_id": user_id, **limiter.limiter.status(str(user_id))}
