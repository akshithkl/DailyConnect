from io import BytesIO
from pathlib import Path
from uuid import uuid4

import cloudinary
import cloudinary.uploader
import cloudinary.utils
from fastapi import HTTPException, UploadFile, status
from PIL import Image, ImageOps

from app.core.config import settings

ALLOWED_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_BYTES = 5 * 1024 * 1024
MAX_IMAGE_DIMENSION = 1600
JPEG_QUALITY = 80
LOCAL_UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"


def compress_image(data: bytes) -> bytes:
    with Image.open(BytesIO(data)) as original:
        image = ImageOps.exif_transpose(original)
        image.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), Image.Resampling.LANCZOS)
        if image.mode not in ("RGB", "L"):
            background = Image.new("RGB", image.size, "white")
            background.paste(image, mask=image.getchannel("A") if "A" in image.getbands() else None)
            image = background
        elif image.mode == "L":
            image = image.convert("RGB")
        output = BytesIO()
        image.save(output, format="JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
        return output.getvalue()


def cloudinary_configured() -> bool:
    return bool(settings.cloudinary_url)


def configure_cloudinary() -> None:
    cloudinary.config(cloudinary_url=settings.cloudinary_url, secure=True)


async def upload_image(file: UploadFile, prefix: str) -> str:
    data = await file.read()
    if len(data) > MAX_BYTES or file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Use JPG, PNG, or WEBP under 5 MB")
    try:
        with Image.open(BytesIO(data)) as image:
            image.verify()
        data = compress_image(data)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image") from exc
    key = f"{prefix}/{uuid4().hex}.jpg"
    if not cloudinary_configured():
        local_file = LOCAL_UPLOAD_DIR / key
        local_file.parent.mkdir(parents=True, exist_ok=True)
        local_file.write_bytes(data)
        return key
    configure_cloudinary()
    result = cloudinary.uploader.upload(BytesIO(data), folder=prefix, resource_type="image", format="jpg", quality="auto")
    return result["public_id"]


def public_url(key: str | None) -> str | None:
    if not key:
        return None
    if cloudinary_configured():
        configure_cloudinary()
        return cloudinary.utils.cloudinary_url(key, secure=True, resource_type="image", format="jpg")[0]
    return f"{settings.api_url.rstrip('/')}/uploads/{key}"


def delete_image(key: str) -> None:
    if cloudinary_configured():
        configure_cloudinary()
        cloudinary.uploader.destroy(key, resource_type="image")
        return
    local_file = LOCAL_UPLOAD_DIR / key
    if local_file.exists():
        local_file.unlink()
