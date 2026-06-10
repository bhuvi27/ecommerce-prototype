from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Beauty Store Service"
    debug: bool = True
    api_prefix: str = "api/v1"
    cors_origins: str = "http://localhost:3001"

    kafka_bootstrap_servers: str = Field(default="localhost:9092", validation_alias="KAFKA_BOOTSTRAP_SERVERS")
    catalog_service_url: str = Field(default="", validation_alias="CATALOG_SERVICE_URL")
    cart_service_url: str = Field(default="", validation_alias="CART_SERVICE_URL")
    payment_service_url: str = Field(default="", validation_alias="PAYMENT_SERVICE_URL")
    order_service_url: str = Field(default="", validation_alias="ORDER_SERVICE_URL")

    database_url: str = Field(
        default="postgresql+asyncpg://beauty:beauty@localhost:5432/beauty_store",
        validation_alias="DATABASE_URL",
    )
    mongodb_uri: str = Field(default="mongodb://localhost:27017", validation_alias="MONGODB_URI")
    mongodb_db: str = Field(default="beauty_catalog", validation_alias="MONGODB_DB")
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")

    jwt_access_secret: str = Field(default="dev-access-secret-change-in-production-32chars", validation_alias="JWT_ACCESS_SECRET")
    jwt_refresh_secret: str = Field(default="dev-refresh-secret-change-in-production-32chars", validation_alias="JWT_REFRESH_SECRET")

    s3_endpoint: str = Field(default="http://localhost:9000", validation_alias="S3_ENDPOINT")
    s3_region: str = Field(default="us-east-1", validation_alias="S3_REGION")
    s3_bucket: str = Field(default="beauty-products", validation_alias="S3_BUCKET")
    s3_access_key: str = Field(default="minioadmin", validation_alias="S3_ACCESS_KEY")
    s3_secret_key: str = Field(default="minioadmin", validation_alias="S3_SECRET_KEY")
    s3_public_url: str = Field(default="http://localhost:9000/beauty-products", validation_alias="S3_PUBLIC_URL")
    s3_force_path_style: bool = Field(default=True, validation_alias="S3_FORCE_PATH_STYLE")

    razorpay_key_id: str = Field(default="", validation_alias="RAZORPAY_KEY_ID")
    razorpay_key_secret: str = Field(default="", validation_alias="RAZORPAY_KEY_SECRET")
    razorpay_webhook_secret: str = Field(default="", validation_alias="RAZORPAY_WEBHOOK_SECRET")
    enable_cod: bool = Field(default=True, validation_alias="ENABLE_COD")

    smtp_host: str = Field(default="", validation_alias="SMTP_HOST")
    smtp_port: int = Field(default=587, validation_alias="SMTP_PORT")
    smtp_user: str = Field(default="", validation_alias="SMTP_USER")
    smtp_pass: str = Field(default="", validation_alias="SMTP_PASS")
    email_from: str = Field(default="noreply@beauty-store.local", validation_alias="EMAIL_FROM")

    cart_ttl_days: int = 30
    catalog_cache_ttl: int = 120
    order_expire_hours: int = 24

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def monolith_env(self) -> dict[str, str]:
        """Map service settings to monolith Settings env keys."""
        url = self.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        return {
            "DATABASE_URL": url,
            "MONGODB_URI": self.mongodb_uri,
            "MONGODB_DB": self.mongodb_db,
            "REDIS_URL": self.redis_url,
            "CORS_ORIGINS": self.cors_origins,
            "JWT_ACCESS_SECRET": self.jwt_access_secret,
            "JWT_REFRESH_SECRET": self.jwt_refresh_secret,
            "S3_ENDPOINT": self.s3_endpoint,
            "S3_REGION": self.s3_region,
            "S3_BUCKET": self.s3_bucket,
            "S3_ACCESS_KEY": self.s3_access_key,
            "S3_SECRET_KEY": self.s3_secret_key,
            "S3_PUBLIC_URL": self.s3_public_url,
            "S3_FORCE_PATH_STYLE": str(self.s3_force_path_style).lower(),
            "RAZORPAY_KEY_ID": self.razorpay_key_id,
            "RAZORPAY_KEY_SECRET": self.razorpay_key_secret,
            "RAZORPAY_WEBHOOK_SECRET": self.razorpay_webhook_secret,
            "ENABLE_COD": str(self.enable_cod).lower(),
            "SMTP_HOST": self.smtp_host,
            "SMTP_PORT": str(self.smtp_port),
            "SMTP_USER": self.smtp_user,
            "SMTP_PASS": self.smtp_pass,
            "EMAIL_FROM": self.email_from,
        }


def apply_monolith_env() -> None:
    import os

    settings = get_service_settings()
    for key, value in settings.monolith_env().items():
        os.environ.setdefault(key, value)

    template = os.environ.get("DATABASE_URL_TEMPLATE", "")
    password = os.environ.get("DB_PASSWORD", "")
    if template and password and "__PASSWORD__" in template:
        os.environ["DATABASE_URL"] = template.replace("__PASSWORD__", password)

    redis_host = os.environ.get("REDIS_HOST")
    redis_port = os.environ.get("REDIS_PORT", "6379")
    if redis_host:
        os.environ.setdefault("REDIS_URL", f"redis://{redis_host}:{redis_port}/0")

    kafka = os.environ.get("KAFKA_BOOTSTRAP_SERVERS") or os.environ.get("KAFKA_BOOTSTRAP")
    if kafka:
        os.environ.setdefault("KAFKA_BOOTSTRAP_SERVERS", kafka)

    mongo_uri = os.environ.get("MONGO_URI")
    if mongo_uri:
        os.environ.setdefault("MONGODB_URI", mongo_uri)


@lru_cache
def get_service_settings() -> ServiceSettings:
    return ServiceSettings()
