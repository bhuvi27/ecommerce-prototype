from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Beauty Store API"
    debug: bool = True
    api_prefix: str = "api/v1"
    cors_origins: str = "http://localhost:3001"

    database_url: str = "postgresql+asyncpg://beauty:beauty@localhost:5432/beauty_store"
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "beauty_catalog"
    redis_url: str = "redis://localhost:6379/0"

    jwt_access_secret: str = "dev-access-secret-change-in-production-32chars"
    jwt_refresh_secret: str = "dev-refresh-secret-change-in-production-32chars"
    jwt_access_expire_minutes: int = 15
    jwt_refresh_expire_days: int = 7

    s3_endpoint: str = "http://localhost:9000"
    s3_region: str = "us-east-1"
    s3_bucket: str = "beauty-products"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_public_url: str = "http://localhost:9000/beauty-products"
    s3_force_path_style: bool = True

    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    email_from: str = "noreply@beauty-store.local"

    admin_email: str = "admin@beauty-store.local"
    admin_password: str = "Admin123!"

    cart_ttl_days: int = 30
    catalog_cache_ttl: int = 120
    order_expire_hours: int = 24

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if s.database_url.startswith("postgres://"):
        return s.model_copy(
            update={"database_url": s.database_url.replace("postgres://", "postgresql+asyncpg://", 1)}
        )
    return s
