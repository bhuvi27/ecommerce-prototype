from pydantic import BaseModel, Field


class CategoryResponse(BaseModel):
    id: str
    slug: str
    name: str
    description: str | None = None


class ProductSkuResponse(BaseModel):
    id: str
    label: str
    price: int
    currency: str = "INR"


class ProductResponse(BaseModel):
    id: str
    slug: str
    name: str
    description: str | None
    category_id: str
    category_slug: str
    status: str
    image_url: str | None
    skus: list[ProductSkuResponse]
    attributes: dict = Field(default_factory=dict)


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    next_cursor: str | None = None
