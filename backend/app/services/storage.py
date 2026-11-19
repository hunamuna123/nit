import contextlib
import io
import json
import logging
import secrets

from fastapi.concurrency import run_in_threadpool
from minio import Minio
from minio.error import S3Error

from app.core.config import get_settings

log = logging.getLogger("nit.storage")

ALLOWED = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp", "image/gif": "gif"}


def _client() -> Minio:
    s = get_settings()
    return Minio(
        s.s3_endpoint,
        access_key=s.s3_access_key,
        secret_key=s.s3_secret_key,
        secure=s.s3_secure,
        region=s.s3_region,
    )


def _ensure_bucket_sync() -> None:
    s = get_settings()
    c = _client()
    if not c.bucket_exists(s.s3_bucket):
        c.make_bucket(s.s3_bucket)
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": ["*"]},
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{s.s3_bucket}/*"],
            }
        ],
    }
    with contextlib.suppress(S3Error):
        c.set_bucket_policy(s.s3_bucket, json.dumps(policy))


async def ensure_bucket() -> None:
    try:
        await run_in_threadpool(_ensure_bucket_sync)
    except Exception as e:  # s3 может быть не поднят, апи все равно стартует
        log.warning("S3 недоступно: %s", e)


def _put_sync(key: str, data: bytes, content_type: str) -> None:
    _client().put_object(
        get_settings().s3_bucket, key, io.BytesIO(data), len(data), content_type=content_type
    )


async def save_image(data: bytes, content_type: str, user_id: int) -> str:
    ext = ALLOWED[content_type]
    key = f"u{user_id}/{secrets.token_hex(10)}.{ext}"
    await run_in_threadpool(_put_sync, key, data, content_type)
    return f"{get_settings().media_url_prefix}/{key}"
