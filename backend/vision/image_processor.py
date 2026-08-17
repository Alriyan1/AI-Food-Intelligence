import cv2
import numpy as np
from PIL import Image,ExifTags
from typing import Tuple,Dict,Optional
from loguru import logger
import io

class ImageProcessor:
    def __init__(self,max_size:int=1920,min_size:int=512):
        self.max_size = max_size
        self.min_size = min_size

    def load_image(self,image_bytes:bytes) -> Tuple[np.ndarray,Dict]:

        image = Image.open(io.BytesIO(image_bytes))

        image = self._correct_exif(image)

        image_np = np.array(image)

        quality_metrics = self._assess_quality(image_np)

        image_np = self._resize_image(image_np)

        image_normalized = self._normalize_image(image_np)

        return image_normalized, quality_metrics

    def _correct_exif(self,image:Image.Image) -> Image.Image:
        try:
            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation] == 'Orientation':
                    break

            exif = image._getexif()
            if exif:
                orientation_value = exif.get(orientation)

                if orientation_value == 3:
                    image = image.rotate(180,expand=True)
                elif orientation_value == 6:
                    image = image.rotate(270,expand=True)
                elif orientation_value == 8:
                    image = image.rotate(90,expand=True)

        except Exception as e:
            logger.warning(f"EXIF correction failed: {e}")

        return image

    def _assess_quality(self,image:np.ndarray) -> Dict:
        gray = cv2.cvtColor(image,cv2.COLOR_RGB2GRAY)

        blur_score = cv2.Laplacian(gray,cv2.CV_64F).var()

        brightness = np.mean(gray)

        contrast = np.std(gray)

        quality_score = self._calculate_quality_score(blur_score,brightness,contrast)

        return {
            'blur_score': float(blur_score),
            'brightness': float(brightness),
            'contrast': float(contrast),
            'quality_score': quality_score,
            'is_acceptable': quality_score>0.3,
            'warnings': self._generate_warnings(blur_score,brightness,contrast)
        }

    def _calculate_quality_score(self,blur: float,brightness: float,contrast: float)->float:

        blur_norm = min(blur / 500, 1.0) #higher blur score = less blur
        brightness_norm = 1.0 - abs(brightness - 128)/128
        contrast_norm = min(contrast/50,1.0)

        score = 0.5 *blur_norm + 0.3 * brightness_norm +0.2 * contrast_norm
        return max(0.0,min(1.0,score))

    def _generate_warnings(self, blur:float,brightness: float,contrast:float)->list:
        warnings = []

        if blur < 100:
            warnings.append('Image appears blurry. Consider retaking with better focus.')

        if brightness<50:
            warnings.append("Image is too dark. Better lighting recommended.")
        elif brightness > 200:
            warnings.append('Image is too bright. Avoid overexposure.')

        if contrast<20:
            warnings.append('Image has low contrast.')

        return warnings

    def _resize_image(self,image:np.ndarray)->np.ndarray:

        height, width = image.shape[:2]

        if max(height,width) > self.max_size:
            scale = self.max_size/max(height,width)
        elif min(height,width) < self.min_size:
            scale = self.min_size / min(height,width)
        else:
            scale = 1.0

        if scale !=1.0:
            new_width = int(width*scale)
            new_heigth = int(height*scale)
            image = cv2.resize(image,(new_width,new_heigth),interpolation=cv2.INTER_AREA)

        return image

    def _normalize_image(self,image:np.ndarray)->np.ndarray:

        image_float = image.astype(np.float32)/255.0
        return image_float

    