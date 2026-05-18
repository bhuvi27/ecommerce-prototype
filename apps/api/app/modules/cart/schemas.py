import uuid
from pydantic import BaseModel, Field


class CartItemInput(BaseModel):
    product_id: str
    sku_id: str
    quantity: int = Field(ge=1, le=10)


class CartItemResponse(BaseModel):
    product_id: str
    sku_id: str
    product_name: str
    unit_price: int
    quantity: int
    image_url: str | None
    line_total: int


class CartResponse(BaseModel):
    cart_id: str
    items: list[CartItemResponse]
    subtotal: int
    item_count: int
