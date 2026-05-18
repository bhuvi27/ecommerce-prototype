"""initial schema

Revision ID: 001
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255)),
        sa.Column("role", sa.Enum("customer", "admin", name="userrole"), nullable=False),
        sa.Column("failed_logins", sa.Integer(), default=0),
        sa.Column("locked_until", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "refresh_tokens",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("token_hash", sa.String(255)),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "addresses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("label", sa.String(100)),
        sa.Column("line1", sa.String(255)),
        sa.Column("line2", sa.String(255)),
        sa.Column("city", sa.String(100)),
        sa.Column("state", sa.String(100)),
        sa.Column("pincode", sa.String(20)),
        sa.Column("phone", sa.String(20)),
        sa.Column("is_default", sa.Boolean()),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "carts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True),
        sa.Column("guest_id", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_carts_guest_id", "carts", ["guest_id"])
    op.create_table(
        "cart_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("cart_id", UUID(as_uuid=True), sa.ForeignKey("carts.id", ondelete="CASCADE")),
        sa.Column("product_id", sa.String(64)),
        sa.Column("sku_id", sa.String(64)),
        sa.Column("product_name", sa.String(255)),
        sa.Column("unit_price", sa.Integer()),
        sa.Column("quantity", sa.Integer()),
        sa.Column("image_url", sa.String(512)),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("cart_id", "product_id", "sku_id"),
    )
    op.create_table(
        "orders",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("status", sa.Enum("pending", "payment_failed", "confirmed", "cancelled", "expired", name="orderstatus")),
        sa.Column("idempotency_key", sa.String(128), unique=True),
        sa.Column("subtotal", sa.Integer()),
        sa.Column("currency", sa.String(8)),
        sa.Column("shipping_name", sa.String(255)),
        sa.Column("shipping_phone", sa.String(20)),
        sa.Column("shipping_line1", sa.String(255)),
        sa.Column("shipping_line2", sa.String(255)),
        sa.Column("shipping_city", sa.String(100)),
        sa.Column("shipping_state", sa.String(100)),
        sa.Column("shipping_pincode", sa.String(20)),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "order_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("order_id", UUID(as_uuid=True), sa.ForeignKey("orders.id", ondelete="CASCADE")),
        sa.Column("product_id", sa.String(64)),
        sa.Column("sku_id", sa.String(64)),
        sa.Column("product_name", sa.String(255)),
        sa.Column("unit_price", sa.Integer()),
        sa.Column("quantity", sa.Integer()),
        sa.Column("image_url", sa.String(512)),
    )
    op.create_table(
        "payments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("order_id", UUID(as_uuid=True), sa.ForeignKey("orders.id", ondelete="CASCADE")),
        sa.Column("status", sa.Enum("created", "pending", "captured", "failed", "refunded", name="paymentstatus")),
        sa.Column("amount", sa.Integer()),
        sa.Column("currency", sa.String(8)),
        sa.Column("razorpay_order_id", sa.String(64), unique=True),
        sa.Column("razorpay_payment_id", sa.String(64), unique=True),
        sa.Column("raw_webhook", JSON),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "idempotency_keys",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("key", sa.String(128), unique=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("response_body", JSON),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "outbox_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("event_type", sa.String(64)),
        sa.Column("payload", JSON),
        sa.Column("status", sa.String(32)),
        sa.Column("attempts", sa.Integer()),
        sa.Column("last_error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_outbox_status_created", "outbox_events", ["status", "created_at"])


def downgrade() -> None:
    for t in ["outbox_events", "idempotency_keys", "payments", "order_items", "orders", "cart_items", "carts", "addresses", "refresh_tokens", "users"]:
        op.drop_table(t)
