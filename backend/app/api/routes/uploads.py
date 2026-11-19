from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.api.deps import CurrentUserDep
from app.core.config import get_settings
from app.schemas import UploadOut
from app.services import storage

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/image", status_code=status.HTTP_201_CREATED)
async def upload_image(file: Annotated[UploadFile, File()], user: CurrentUserDep) -> UploadOut:
    content_type = (file.content_type or "").lower()
    if content_type not in storage.ALLOWED:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Поддерживаются PNG, JPEG, WebP и GIF"
        )
    limit = get_settings().upload_max_mb * 1024 * 1024
    data = await file.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE, f"Файл больше {get_settings().upload_max_mb} МБ"
        )
    try:
        url = await storage.save_image(data, content_type, user.id)
    except Exception as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Хранилище недоступно") from e
    return UploadOut(url=url)
