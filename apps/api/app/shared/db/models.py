import enum
import uuid
from datetime import datetime
from sqlalchemy import (
    String, Integer, Boolean, DateTime, ForeignKey, Text, Enum as SAEnum, JSON, UniqueConstraint, Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.shared.db.base import Base


class UserRole(str, enum.Enum):
    customer = "customer"
    admin = "admin"


class OrderStatus(str, enum.Enum):
    pending = "pending"
    payment_failed = "payment_failed"
    confirmed = "confirmed"
    cancelled = "cancelled"
    expired = "expired"


class PaymentStatus(str, enum.Enum):
    created = "created"
    pending = "pending"
    captured = "captured"
    failed = "failed"
    refunded = "refunded"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.customer)
    failed_logins: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    addresses: Mapped[list["Address"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    carts: Mapped[list["Cart"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    orders: Mapped[list["Order"]] = relationship(back_populates="user")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(String(255))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")


class Address(Base):
    __tablename__ = "addresses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    line1: Mapped[str] = mapped_column(String(255))
    line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(100))
    pincode: Mapped[str] = mapped_column(String(20))
    phone: Mapped[str] = mapped_column(String(20))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="addresses")


class Cart(Base):
    __tablename__ = "carts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, unique=True)
    guest_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User | None"] = relationship(back_populates="carts")
    items: Mapped[list["CartItem"]] = relationship(back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = (UniqueConstraint("cart_id", "product_id", "sku_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cart_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("carts.id", ondelete="CASCADE"))
    product_id: Mapped[str] = mapped_column(String(64))
    sku_id: Mapped[str] = mapped_column(String(64))
    product_name: Mapped[str] = mapped_column(String(255))
    unit_price: Mapped[int] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(Integer)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    cart: Mapped["Cart"] = relationship(back_populates="items")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    status: Mapped[OrderStatus] = mapped_column(SAEnum(OrderStatus), default=OrderStatus.pending)
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True)
    subtotal: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(8), default="INR")
    shipping_name: Mapped[str] = mapped_column(String(255))
    shipping_phone: Mapped[str] = mapped_column(String(20))
    shipping_line1: Mapped[str] = mapped_column(String(255))
    shipping_line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    shipping_city: Mapped[str] = mapped_column(String(100))
    shipping_state: Mapped[str] = mapped_column(String(100))
    shipping_pincode: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User | None"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    payments: Mapped[list["Payment"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"))
    product_id: Mapped[str] = mapped_column(String(64))
    sku_id: Mapped[str] = mapped_column(String(64))
    product_name: Mapped[str] = mapped_column(String(255))
    unit_price: Mapped[int] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(Integer)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    order: Mapped["Order"] = relationship(back_populates="items")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"))
    status: Mapped[PaymentStatus] = mapped_column(SAEnum(PaymentStatus), default=PaymentStatus.created)
    amount: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(8), default="INR")
    razorpay_order_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    razorpay_payment_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    raw_webhook: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    order: Mapped["Order"] = relationship(back_populates="payments")


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(128), unique=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    response_body: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    __table_args__ = (Index("ix_outbox_status_created", "status", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
