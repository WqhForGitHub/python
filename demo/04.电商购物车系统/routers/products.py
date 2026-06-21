"""商品路由（带 Redis 缓存）。"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

import cache
import crud.product
import schemas
from database import get_db

router = APIRouter(prefix="/products", tags=["商品"])


@router.post(
    "/",
    response_model=schemas.ProductRead,
    status_code=status.HTTP_201_CREATED,
    summary="创建商品",
)
def create_product(product_in: schemas.ProductCreate, db: Session = Depends(get_db)):
    return crud.product.create_product(db, product_in)


@router.get(
    "/",
    summary="商品列表（分页，支持关键词）",
)
def list_products(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    keyword: str | None = Query(None, description="商品名关键词"),
    db: Session = Depends(get_db),
):
    items, total = crud.product.list_products(db, page=page, size=size, keyword=keyword)
    pages = (total + size - 1) // size if total else 0
    return {
        "items": items,
        "meta": {"page": page, "size": size, "total": total, "pages": pages},
        "cache": "redis" if cache.is_redis_available() else "memory",
    }


@router.get(
    "/{product_id}",
    response_model=schemas.ProductRead,
    summary="商品详情（带缓存）",
)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = crud.product.get_product_cached(db, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail=f"商品 ID {product_id} 不存在")
    return product


@router.put(
    "/{product_id}",
    response_model=schemas.ProductRead,
    summary="更新商品",
)
def update_product(
    product_id: int,
    product_in: schemas.ProductUpdate,
    db: Session = Depends(get_db),
):
    product = crud.product.get_product(db, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail=f"商品 ID {product_id} 不存在")
    return crud.product.update_product(db, product, product_in)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除商品",
)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = crud.product.get_product(db, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail=f"商品 ID {product_id} 不存在")
    crud.product.delete_product(db, product)
    return None
