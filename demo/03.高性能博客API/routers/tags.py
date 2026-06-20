"""标签路由。"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

import crud.tag
import schemas
from database import get_db

router = APIRouter(prefix="/tags", tags=["标签"])


@router.post(
    "/",
    response_model=schemas.TagRead,
    status_code=status.HTTP_201_CREATED,
    summary="创建标签",
)
async def create_tag(tag_in: schemas.TagCreate, db: AsyncSession = Depends(get_db)):
    if await crud.tag.get_tag_by_name(db, tag_in.name):
        raise HTTPException(status_code=400, detail="标签已存在")
    return await crud.tag.create_tag(db, tag_in)


@router.get(
    "/",
    response_model=list[schemas.TagRead],
    summary="标签列表",
)
async def list_tags(db: AsyncSession = Depends(get_db)):
    return await crud.tag.get_tags(db)


@router.delete(
    "/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除标签",
)
async def delete_tag(tag_id: int, db: AsyncSession = Depends(get_db)):
    tag = await crud.tag.get_tag(db, tag_id)
    if tag is None:
        raise HTTPException(status_code=404, detail=f"标签 ID {tag_id} 不存在")
    await crud.tag.delete_tag(db, tag)
    return None
