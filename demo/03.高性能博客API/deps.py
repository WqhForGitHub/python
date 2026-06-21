"""FastAPI 依赖项：异步 DB Session。"""

from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db


# 重新导出，便于路由统一从 deps 导入
async def get_session() -> AsyncSession:
    # 这里仅作为占位，真正使用 Depends(get_db)
    async with get_db() as session:
        yield session
