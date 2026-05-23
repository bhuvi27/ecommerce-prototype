import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, model_validator

PaymentMethod = Literal["cod", "online"]


class CheckoutRequest(BaseModel):
    payment_method: PaymentMethod = "cod"
    address_id: uuid.UUID | None = None
    save_address: bool = False
    address_label: str | None = None
    shipping_name: str | None = None
    shipping_phone: str | None = None
    shipping_line1: str | None = None
    shipping_line2: str | None = None
    shipping_city: str | None = None
    shipping_state: str | None = None
    shipping_pincode: str | None = None

    @model_validator(mode="after")
    def require_shipping_or_address(self):
        if self.address_id:
            return self
        required = (
            "shipping_name", "shipping_phone", "shipping_line1",
            "shipping_city", "shipping_state", "shipping_pincode",
        )
        missing = [f for f in required if not getattr(self, f)]
        if missing:
            raise ValueError(f"Missing shipping fields: {', '.join(missing)}")
        return self


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
    payment_method: str | None = None
    razorpay_order_id: str | None = None
    razorpay_key_id: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class CheckoutResponse(BaseModel):
    order: OrderResponse
    payment_method: str
    razorpay_order_id: str | None = None
    razorpay_key_id: str | None = None
    amount: int
    currency: str
