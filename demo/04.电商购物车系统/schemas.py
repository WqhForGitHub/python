"""Pydantic 模型 (Schema)。"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# 商品
# ============================================================
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, examples=["iPhone 15"])
    description: str = Field("", max_length=2000, examples=["苹果手机"])
    price: Decimal = Field(..., gt=0, description="价格（元）", examples=[6999.00])
    stock: int = Field(0, ge=0, description="库存", examples=[100])
    image_url: str = Field("", max_length=255)
    is_active: bool = Field(True, description="是否上架")


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=2000)
    price: Optional[Decimal] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    image_url: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class ProductRead(BaseModel):
    id: int
    name: str
    description: str
    price: Decimal
    stock: int
    image_url: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# 购物车
# ============================================================
class CartItemIn(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, description="数量，>0")


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., gt=0)


class CartItemOut(BaseModel):
    product_id: int
    product_name: str
    price: Decimal
    quantity: int
    subtotal: Decimal


class CartOut(BaseModel):
    user_id: int
    items: list[CartItemOut]
    total_amount: Decimal


# ============================================================
# 订单
# ============================================================
class OrderItemRead(BaseModel):
    id: int
    product_id: int
    product_name: str
    price: Decimal
    quantity: int

    model_config = ConfigDict(from_attributes=True)


class OrderRead(BaseModel):
    id: int
    user_id: int
    order_no: str
    total_amount: Decimal
    status: str
    address: str
    created_at: datetime
    items: list[OrderItemRead] = []

    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):
    user_id: int = Field(..., gt=0)
    address: str = Field(..., min_length=1, max_length=255)


class Message(BaseModel):
    message: str
