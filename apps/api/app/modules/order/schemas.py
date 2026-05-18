import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class CheckoutRequest(BaseModel):
    shipping_name: str
    shipping_phone: str
    shipping_line1: str
    shipping_line2: str | None = None
    shipping_city: str
    shipping_state: str
    shipping_pincode: str


class OrderItemResponse(BaseModel):
    product_id: str
    sku_id: str
    product_name: str
    unit_price: int
    quantity: int
    image_url: str | None


class OrderResponse(BaseModel):
    id: uuid.UUID
    status: str
    subtotal: int
    currency: str
    items: list[OrderItemResponse]
    razorpay_order_id: str | None = None
    razorpay_key_id: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class CheckoutResponse(BaseModel):
    order: OrderResponse
    razorpay_order_id: str
    razorpay_key_id: str
    amount: int
    currency: str
