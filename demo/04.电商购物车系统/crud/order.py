"""订单 CRUD 操作。"""
import time
import uuid

from sqlalchemy.orm import Session

import cache
import crud.cart
import crud.product
import models
import schemas


def generate_order_no() -> str:
    """生成唯一订单号：时间戳 + UUID 片段。"""
    return f"ORD{time.strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"


def get_order(db: Session, order_id: int) -> models.Order | None:
    return db.query(models.Order).filter(models.Order.id == order_id).first()


def get_order_by_no(db: Session, order_no: str) -> models.Order | None:
    return db.query(models.Order).filter(models.Order.order_no == order_no).first()


def list_orders(
    db: Session, user_id: int | None = None, page: int = 1, size: int = 10
) -> tuple[list[models.Order], int]:
    stmt = db.query(models.Order)
    if user_id is not None:
        stmt = stmt.filter(models.Order.user_id == user_id)
    total = stmt.count()
    items = (
        stmt.order_by(models.Order.id.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    return items, total


def create_order_from_cart(
    db: Session, user_id: int, address: str
) -> models.Order:
    """从购物车生成订单。

    流程：
    1. 读取购物车
    2. 校验商品 / 库存
    3. 扣减库存
    4. 生成订单与订单明细
    5. 清空购物车
    """
    cart = crud.cart.get_cart(db, user_id)
    if not cart.items:
        raise ValueError("购物车为空，无法下单")

    # 二次校验库存并扣减
    for item in cart.items:
        ok = crud.product.decrease_stock(db, item.product_id, item.quantity)
        if not ok:
            raise ValueError(
                f"商品 {item.product_name} 库存不足，下单失败"
            )

    total_amount = cart.total_amount
    order = models.Order(
        user_id=user_id,
        order_no=generate_order_no(),
        total_amount=total_amount,
        status="pending",
        address=address,
    )
    for item in cart.items:
        order.items.append(
            models.OrderItem(
                product_id=item.product_id,
                product_name=item.product_name,
                price=item.price,
                quantity=item.quantity,
            )
        )
    db.add(order)
    db.commit()
    db.refresh(order)

    # 清空购物车
    crud.cart.clear(user_id)
    return order


def cancel_order(db: Session, order: models.Order) -> models.Order:
    """取消订单并归还库存。"""
    if order.status != "pending":
        raise ValueError(f"订单状态为 {order.status}，无法取消")
    for item in order.items:
        product = crud.product.get_product(db, item.product_id)
        if product:
            product.stock += item.quantity
    order.status = "cancelled"
    db.commit()
    db.refresh(order)
    return order


def pay_order(db: Session, order: models.Order) -> models.Order:
    if order.status != "pending":
        raise ValueError(f"订单状态为 {order.status}，无法支付")
    order.status = "paid"
    db.commit()
    db.refresh(order)
    return order
