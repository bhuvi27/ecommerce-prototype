from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    slug: str
    name: str
    description: str | None = None


class SkuCreate(BaseModel):
    id: str
    label: str
    price: int
    currency: str = "INR"


class ProductCreate(BaseModel):
    slug: str
    name: str
    description: str | None = None
    category_slug: str
    status: str = "active"
    image_url: str | None = None
    skus: list[SkuCreate]
    attributes: dict = Field(default_factory=dict)


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    image_url: str | None = None
    skus: list[SkuCreate] | None = None
    attributes: dict | None = None
