import uuid
from functools import lru_cache
import boto3
from botocore.client import Config
from app.config import get_settings


@lru_cache
def _client():
    s = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=s.s3_endpoint,
        aws_access_key_id=s.s3_access_key,
        aws_secret_access_key=s.s3_secret_key,
        region_name=s.s3_region,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path" if s.s3_force_path_style else "auto"}),
    )


def upload_bytes(data: bytes, content_type: str, folder: str = "products") -> str:
    s = get_settings()
    key = f"{folder}/{uuid.uuid4().hex}"
    _client().put_object(Bucket=s.s3_bucket, Key=key, Body=data, ContentType=content_type)
    return f"{s.s3_public_url.rstrip('/')}/{key}"
