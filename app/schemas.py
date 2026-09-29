from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OrderStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"


class CustomerCreate(BaseModel):
    email: str = Field(min_length=3, max_length=320, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    name: str = Field(min_length=1, max_length=120)
    country_code: str = Field(min_length=2, max_length=2)

    @field_validator("country_code")
    @classmethod
    def normalize_country(cls, value: str) -> str:
        return value.upper()


class Customer(CustomerCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime


class OrderItemCreate(BaseModel):
    product_id: UUID
    quantity: int = Field(gt=0, le=100)


class OrderCreate(BaseModel):
    customer_id: UUID
    items: list[OrderItemCreate] = Field(min_length=1, max_length=50)


class OrderItem(BaseModel):
    product_id: UUID
    sku: str
    product_name: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal


class Order(BaseModel):
    id: UUID
    customer_id: UUID
    status: OrderStatus
    total_amount: Decimal
    created_at: datetime
    items: list[OrderItem]


class EventCreate(BaseModel):
    event_id: UUID
    customer_id: UUID | None = None
    session_id: str = Field(min_length=1, max_length=100)
    event_type: str = Field(pattern=r"^(page_view|product_view|search|add_to_cart|checkout_started)$")
    occurred_at: datetime
    properties: dict = Field(default_factory=dict)


class FunnelMetrics(BaseModel):
    product_views: int
    add_to_carts: int
    checkouts: int
    purchases: int
    view_to_cart_rate: float
    cart_to_purchase_rate: float

