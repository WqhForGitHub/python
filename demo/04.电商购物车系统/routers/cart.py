"""购物车路由（Redis 存储）。

通过 header `X-User-Id` 标识用户（Demo 简化，实际应接入鉴权）。
"""

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

import crud.cart
import schemas
from database import get_db

router = APIRouter(prefix="/cart", tags=["购物车"])


def _require_user(x_user_id: int | None = Header(None, alias="X-User-Id")) -> int:
    if x_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请在请求头携带 X-User-Id",
        )
    return x_user_id


@router.get("/", response_model=schemas.CartOut, summary="查看购物车")
def get_cart(
    db: Session = Depends(get_db),
    user_id: int = Depends(_require_user),
):
    return crud.cart.get_cart(db, user_id)


@router.post(
    "/items",
    response_model=schemas.CartOut,
    summary="加入购物车",
)
def add_item(
    item: schemas.CartItemIn,
    db: Session = Depends(get_db),
    user_id: int = Depends(_require_user),
):
    try:
        return crud.cart.add_item(db, user_id, item)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put(
    "/items/{product_id}",
    response_model=schemas.CartOut,
    summary="修改购物车商品数量",
)
def update_item(
    product_id: int,
    body: schemas.CartItemUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(_require_user),
):
    try:
        return crud.cart.update_item(db, user_id, product_id, body.quantity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/items/{product_id}",
    response_model=schemas.CartOut,
    summary="移除购物车商品",
)
def remove_item(
    product_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(_require_user),
):
    return crud.cart.remove_item(db, user_id, product_id)


@router.delete(
    "/",
    response_model=schemas.Message,
    summary="清空购物车",
)
def clear_cart(
    user_id: int = Depends(_require_user),
):
    crud.cart.clear(user_id)
    return {"message": "购物车已清空"}
