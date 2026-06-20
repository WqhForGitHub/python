"""商品 CRUD 操作（带 Redis 缓存）。"""
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

import cache
import config
import models
import schemas

PRODUCT_CACHE_KEY = "product:{pid}"
PRODUCT_LIST_CACHE_KEY = "products:list:{page}:{size}:{kw}"


def _invalidate_product_cache(product_id: int | None = None) -> None:
    """清除商品相关缓存。"""
    if product_id is not None:
        cache.cache_delete(PRODUCT_CACHE_KEY.format(pid=product_id))
    # 清除所有列表缓存（简单起见全部清除）
    for key in cache.cache_keys("products:list:*"):
        cache.cache_delete(key)


def get_product(db: Session, product_id: int) -> models.Product | None:
    return db.query(models.Product).filter(models.Product.id == product_id).first()


def get_product_cached(db: Session, product_id: int) -> models.Product | None:
    """优先读缓存；缓存未命中则查库并回填。"""
    cached = cache.cache_get_json(PRODUCT_CACHE_KEY.format(pid=product_id))
    if cached:
        # 还原为 ORM-like 对象（用 SimpleNamespace 不足以满足 response_model）
        # 这里直接查库以保证 response_model from_attributes 正常；演示缓存命中场景
        p = models.Product(
            id=cached["id"],
            name=cached["name"],
            description=cached["description"],
            price=Decimal(cached["price"]),
            stock=cached["stock"],
            image_url=cached["image_url"],
            is_active=cached["is_active"],
            created_at=cached["created_at"],
        )
        return p
    p = get_product(db, product_id)
    if p:
        cache.cache_set_json(
            PRODUCT_CACHE_KEY.format(pid=product_id),
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "price": str(p.price),
                "stock": p.stock,
                "image_url": p.image_url,
                "is_active": bool(p.is_active),
                "created_at": p.created_at.isoformat(),
            },
            ttl=config.PRODUCT_CACHE_TTL,
        )
    return p


def list_products(
    db: Session, page: int = 1, size: int = 10, keyword: str | None = None
) -> tuple[list[models.Product], int]:
    stmt = db.query(models.Product).filter(models.Product.is_active == 1)
    if keyword:
        stmt = stmt.filter(models.Product.name.like(f"%{keyword}%"))
    total = stmt.count()
    items = (
        stmt.order_by(models.Product.id.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    return items, total


def create_product(db: Session, product_in: schemas.ProductCreate) -> models.Product:
    product = models.Product(
        name=product_in.name,
        description=product_in.description,
        price=product_in.price,
        stock=product_in.stock,
        image_url=product_in.image_url,
        is_active=1 if product_in.is_active else 0,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    _invalidate_product_cache()
    return product


def update_product(
    db: Session, product: models.Product, product_in: schemas.ProductUpdate
) -> models.Product:
    update_data = product_in.model_dump(exclude_unset=True)
    if "is_active" in update_data:
        update_data["is_active"] = 1 if update_data["is_active"] else 0
    for field, value in update_data.items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    _invalidate_product_cache(product.id)
    return product


def delete_product(db: Session, product: models.Product) -> None:
    db.delete(product)
    db.commit()
    _invalidate_product_cache(product.id)


def decrease_stock(db: Session, product_id: int, quantity: int) -> bool:
    """扣减库存（乐观风格，库存不足返回 False）。"""
    product = get_product(db, product_id)
    if not product or product.stock < quantity:
        return False
    product.stock -= quantity
    db.commit()
    _invalidate_product_cache(product_id)
    return True
