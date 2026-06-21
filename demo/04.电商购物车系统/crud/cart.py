"""购物车操作（基于 Redis / 内存缓存）。

购物车不落库，结构为：
    key  : cart:{user_id}
    value: Hash { product_id: quantity }
"""

from decimal import Decimal

from sqlalchemy.orm import Session

import cache
import crud.product
import schemas


def get_cart(db: Session, user_id: int) -> schemas.CartOut:
    """读取购物车，并关联商品信息（名称 / 价格）。"""
    raw = cache.cart_get_all(user_id)  # {str(pid): qty}
    items: list[schemas.CartItemOut] = []
    total = Decimal("0")
    for pid_str, qty in raw.items():
        pid = int(pid_str)
        product = crud.product.get_product_cached(db, pid)
        if product is None:
            # 商品已被删除，跳过
            continue
        subtotal = Decimal(product.price) * qty
        items.append(
            schemas.CartItemOut(
                product_id=pid,
                product_name=product.name,
                price=Decimal(product.price),
                quantity=qty,
                subtotal=subtotal,
            )
        )
        total += subtotal
    return schemas.CartOut(user_id=user_id, items=items, total_amount=total)


def add_item(db: Session, user_id: int, item: schemas.CartItemIn) -> schemas.CartOut:
    """加入购物车（若已存在则累加数量）。"""
    product = crud.product.get_product_cached(db, item.product_id)
    if product is None or not product.is_active:
        raise ValueError(f"商品 ID {item.product_id} 不存在或已下架")

    current = cache.cart_get_all(user_id)
    existing_qty = int(current.get(str(item.product_id), 0))
    new_qty = existing_qty + item.quantity
    if new_qty > product.stock:
        raise ValueError(
            f"库存不足，当前库存 {product.stock}，购物车已有 {existing_qty}"
        )
    cache.cart_set_item(user_id, item.product_id, new_qty)
    return get_cart(db, user_id)


def update_item(
    db: Session, user_id: int, product_id: int, quantity: int
) -> schemas.CartOut:
    product = crud.product.get_product_cached(db, product_id)
    if product is None:
        raise ValueError(f"商品 ID {product_id} 不存在")
    if quantity > product.stock:
        raise ValueError(f"库存不足，当前库存 {product.stock}")
    cache.cart_set_item(user_id, product_id, quantity)
    return get_cart(db, user_id)


def remove_item(db: Session, user_id: int, product_id: int) -> schemas.CartOut:
    cache.cart_remove_item(user_id, product_id)
    return get_cart(db, user_id)


def clear(user_id: int) -> None:
    cache.cart_clear(user_id)
