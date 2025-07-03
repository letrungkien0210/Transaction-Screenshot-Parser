"""Image processing and OCR functionality."""

import io
from pathlib import Path
from typing import Tuple

import pytesseract
from loguru import logger
from PIL import Image, ImageEnhance, ImageFilter

from snap_transact.models import OCRSettings


class OCRProcessor:
    """Handles image processing and OCR text extraction."""

    def __init__(self, settings: OCRSettings) -> None:
        """Initialize OCR processor with settings."""
        self.settings = settings
        logger.debug(f"Initialized OCR processor with settings: {settings}")

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image to improve OCR accuracy."""
        if not self.settings.preprocess:
            return image

        logger.debug("Starting image preprocessing")
        
        # Convert to grayscale
        if image.mode != "L":
            image = image.convert("L")
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        
        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(2.0)
        
        # Apply filters to reduce noise
        image = image.filter(ImageFilter.MedianFilter(size=3))
        
        logger.debug("Image preprocessing completed")
        return image

    def extract_text_from_image(self, image_path: Path) -> Tuple[str, float]:
        """Extract text from image using OCR.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        logger.debug(f"Processing image: {image_path}")
        
        try:
            # Load and preprocess image
            with Image.open(image_path) as image:
                # Resize if image is too large
                max_size = (2000, 2000)
                if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                    image.thumbnail(max_size, Image.Resampling.LANCZOS)
                    logger.debug(f"Resized image to: {image.size}")
                
                # Preprocess image
                processed_image = self.preprocess_image(image)
                
                # Configure Tesseract
                config = f'--oem {self.settings.oem} --psm {self.settings.psm} -l {self.settings.language}'
                
                # Extract text
                text = pytesseract.image_to_string(processed_image, config=config)
                
                # Get confidence data
                try:
                    data = pytesseract.image_to_data(processed_image, config=config, output_type=pytesseract.Output.DICT)
                    confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
                    confidence = avg_confidence / 100.0  # Convert to 0-1 scale
                except Exception as e:
                    logger.warning(f"Could not extract confidence data: {e}")
                    confidence = 0.0
                
                logger.debug(f"Extracted {len(text)} characters with confidence: {confidence:.2f}")
                return text.strip(), confidence
                
        except Exception as e:
            logger.error(f"Failed to process image {image_path}: {e}")
            raise

    def validate_image(self, image_path: Path) -> bool:
        """Validate if image file can be processed.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            True if image is valid, False otherwise
        """
        try:
            # Check file exists
            if not image_path.exists():
                logger.warning(f"Image file does not exist: {image_path}")
                return False
            
            # Check file size
            file_size = image_path.stat().st_size
            if file_size > 10_000_000:  # 10MB limit
                logger.warning(f"Image file too large: {file_size} bytes")
                return False
            
            # Try to open image
            with Image.open(image_path) as image:
                # Verify image format
                if image.format.lower() not in ['png', 'jpeg', 'jpg', 'tiff', 'bmp']:
                    logger.warning(f"Unsupported image format: {image.format}")
                    return False
                
                # Check image dimensions
                if image.size[0] < 50 or image.size[1] < 50:
                    logger.warning(f"Image too small: {image.size}")
                    return False
                
                return True
                
        except Exception as e:
            logger.error(f"Image validation failed for {image_path}: {e}")
            return False 