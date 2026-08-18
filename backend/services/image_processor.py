import base64
import io
from typing import Tuple,Optional
from PIL import Image
import cv2
import numpy as np
from loguru import logger

from backend.config import settings

def validate_image(image_bytes: bytes, content_type: str)->Tuple[bool,str]:

    if content_type not in settings.ALLOWED_IMAGE_TYPES:
        return False, f"Unsupported image type: {content_type}. Allowed: {settings.ALLOWED_IMAGE_TYPES}"

    max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(image_bytes) > max_size_bytes:
        return False, f"Image too large: {len(image_bytes)/(1024*1024):.2f} MB. Max: {settings.MAX_UPLOAD_SIZE_MB} MB"

    try:
        Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        return False, f"Invalid image file: {str(e)}"

    return True,""

def preprocess_image(image_bytes:bytes)-> Tuple[bytes,str]:
    img = Image.open(io.BytesIO(image_bytes))

    if img.mode in ("RGBA","P"):
        img = img.convert("RGB")

    max_dimension = 1024
    if max(img.size) > max_dimension:
        ratio = max_dimension/max(img.size)
        new_size = (int(img.size[0]*ratio),int(img.size[1]*ratio))
        img = img.resize(new_size,Image.Resampling.LANCZOS)

    output = io.BytesIO()
    img.save(output, format='JPEG',quality=85,optimize=True)
    output.seek(0)

    return output.getvalue(), 'image/jpeg'

def encode_image_to_base64(image_bytes:bytes)->str:
    return base64.b64encode(image_bytes).decode('utf-8')

def decode_base64_to_image(base64_string: str)->Image.Image:
    image_bytes = base64.b64decode(base64_string)
    return Image.open(io.BytesIO(image_bytes))

def get_image_quality(image_bytes:bytes)->str:
    try:
        img = Image.open(io.BytesIO(image_bytes))
        width,height = img.size

        if width < 224 or height <224:
            return 'poor'
        elif width < 512 or height <512:
            return 'fair'

        if len(image_bytes)<10000:
            return 'fair'

        return 'good'

    except Exception as e:
        logger.error(f"Error assessing image quality: {e}")
        return 'poor'