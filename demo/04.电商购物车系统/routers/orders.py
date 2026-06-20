"""订单路由。"""
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

import crud.order
import schemas
from database import get_db

router = APIRouter(prefix="/orders", tags=["订单"])


@router.post(
    "/",
    response_model=schemas.OrderRead,
    status_code=status.HTTP_201_CREATED,
    summary="从购物车下单",
)
def create_order(
    body: schemas.OrderCreate,
    db: Session = Depends(get_db),
):
    try:
        order = crud.order.create_order_from_cart(db, body.user_id, body.address)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return order


@router.get(
    "/",
    summary="订单列表（分页，可按用户筛选）",
)
def list_orders(
    user_id: int | None = Query(None, description="按用户筛选"),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total = crud.order.list_orders(db, user_id=user_id, page=page, size=size)
    pages = (total + size - 1) // size if total else 0
    return {
        "items": items,
        "meta": {"page": page, "size": size, "total": total, "pages": pages},
    }


@router.get(
    "/{order_id}",
    response_model=schemas.OrderRead,
    summary="订单详情",
)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = crud.order.get_order(db, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail=f"订单 ID {order_id} 不存在")
    return order


@router.post(
    "/{order_id}/pay",
    response_model=schemas.OrderRead,
    summary="支付订单",
)
def pay_order(order_id: int, db: Session = Depends(get_db)):
    order = crud.order.get_order(db, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail=f"订单 ID {order_id} 不存在")
    try:
        return crud.order.pay_order(db, order)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{order_id}/cancel",
    response_model=schemas.OrderRead,
    summary="取消订单（归还库存）",
)
def cancel_order(order_id: int, db: Session = Depends(get_db)):
    order = crud.order.get_order(db, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail=f"订单 ID {order_id} 不存在")
    try:
        return crud.order.cancel_order(db, order)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
