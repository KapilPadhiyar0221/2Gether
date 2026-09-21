"""Shared image validation + downscaling.

Client-side checks are a courtesy; these run on every upload regardless.
"""
import io

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image, ImageOps, UnidentifiedImageError

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP", "GIF"}
MAX_BYTES = getattr(settings, "MAX_IMAGE_UPLOAD_BYTES", 5 * 1024 * 1024)


def validate_image(upload):
    """Verify the bytes really are an image of an allowed type and size."""
    if upload.size > MAX_BYTES:
        raise ValidationError(
            f"That image is {upload.size / 1048576:.1f} MB. Keep it under "
            f"{MAX_BYTES // 1048576} MB."
        )
    try:
        upload.seek(0)
        probe = Image.open(upload)
        probe.verify()  # header check only; invalidates the handle
        fmt = probe.format
    except (UnidentifiedImageError, OSError, ValueError):
        raise ValidationError("That file isn't an image we can read. Try JPG, PNG or WebP.")
    finally:
        upload.seek(0)

    if fmt not in ALLOWED_FORMATS:
        raise ValidationError("Use a JPG, PNG, WebP or GIF image.")
    return upload


def downscale(upload, max_edge=1600, quality=82):
    """Re-encode to a sane size. Returns (file, width, height).

    Animated GIFs pass through untouched so we don't flatten them to one frame.
    """
    upload.seek(0)
    image = Image.open(upload)
    if getattr(image, "is_animated", False):
        upload.seek(0)
        return upload, image.width, image.height

    image = ImageOps.exif_transpose(image)  # honour camera rotation
    has_alpha = image.mode in ("RGBA", "LA", "P")
    image = image.convert("RGBA" if has_alpha else "RGB")
    image.thumbnail((max_edge, max_edge), Image.LANCZOS)

    buffer = io.BytesIO()
    if has_alpha:
        image.save(buffer, format="PNG", optimize=True)
        ext, content_type = "png", "image/png"
    else:
        image.save(buffer, format="JPEG", quality=quality, optimize=True, progressive=True)
        ext, content_type = "jpg", "image/jpeg"
    buffer.seek(0)

    stem = upload.name.rsplit(".", 1)[0][:40] or "image"
    processed = InMemoryUploadedFile(
        buffer, "ImageField", f"{stem}.{ext}", content_type, buffer.getbuffer().nbytes, None
    )
    return processed, image.width, image.height
