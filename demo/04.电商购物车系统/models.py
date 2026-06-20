"""SQLAlchemy ORM 模型。

- Product：商品
- Order：订单
- OrderItem：订单明细（一对多）

购物车不落库，存储在 Redis 中。
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, default="", nullable=False)
    price = Column(Numeric(10, 2), nullable=False)  # 单位：元
    stock = Column(Integer, default=0, nullable=False)
    image_url = Column(String(255), default="", nullable=False)
    is_active = Column(Integer, default=1, nullable=False)  # 1=上架 0=下架
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    # 演示用：用 user_id 标识用户（实际应接入鉴权系统）
    user_id = Column(Integer, nullable=False, index=True)
    order_no = Column(String(32), unique=True, index=True, nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    # pending / paid / cancelled
    address = Column(String(255), default="", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, nullable=False)
    product_name = Column(String(100), nullable=False)  # 下单时的快照
    price = Column(Numeric(10, 2), nullable=False)       # 下单时的快照
    quantity = Column(Integer, nullable=False)

    order = relationship("Order", back_populates="items")
