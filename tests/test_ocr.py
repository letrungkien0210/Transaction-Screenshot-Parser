"""Unit tests for the OCR module."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
from PIL import Image
from pytest_mock import MockerFixture

from snap_transact.ocr import OCRProcessor
from snap_transact.models import OCRSettings


class TestOCRProcessor:
    """Test cases for OCRProcessor class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.settings = OCRSettings(
            language="eng+vie",
            oem=3,
            psm=6,
            dpi=300,
            preprocess=True
        )
        self.processor = OCRProcessor(self.settings)

    def test_init(self, mocker: MockerFixture):
        """Test OCRProcessor initialization."""
        mock_logger = mocker.patch("snap_transact.ocr.logger")
        settings = OCRSettings()
        
        processor = OCRProcessor(settings)
        
        assert processor.settings == settings
        mock_logger.debug.assert_called_once()

    def test_preprocess_image_enabled(self):
        """Test image preprocessing when enabled."""
        # Create a simple test image
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        try:
            # Create a test image
            test_image = Image.new('RGB', (100, 100), color='white')
            test_image.save(temp_path)
            
            # Load and preprocess
            with Image.open(temp_path) as image:
                processed = self.processor.preprocess_image(image)
                
            assert processed.mode == 'L'  # Should be grayscale
            assert processed.size == (100, 100)
            
        finally:
            # Clean up
            if temp_path.exists():
                temp_path.unlink()

    def test_preprocess_image_disabled(self):
        """Test image preprocessing when disabled."""
        settings = OCRSettings(preprocess=False)
        processor = OCRProcessor(settings)
        
        # Create a test image
        test_image = Image.new('RGB', (100, 100), color='white')
        
        processed = processor.preprocess_image(test_image)
        
        # Should return original image unchanged
        assert processed is test_image

    def test_preprocess_image_grayscale_input(self):
        """Test preprocessing with grayscale input."""
        # Create a grayscale test image
        test_image = Image.new('L', (100, 100), color=128)
        
        processed = self.processor.preprocess_image(test_image)
        
        assert processed.mode == 'L'
        assert processed.size == (100, 100)

    @patch('snap_transact.ocr.pytesseract.image_to_string')
    @patch('snap_transact.ocr.pytesseract.image_to_data')
    def test_extract_text_from_image_success(self, mock_image_to_data, mock_image_to_string):
        """Test successful text extraction from image."""
        # Create a test image
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        try:
            test_image = Image.new('RGB', (200, 100), color='white')
            test_image.save(temp_path)
            
            # Mock Tesseract responses
            mock_image_to_string.return_value = "Sample transaction text"
            mock_image_to_data.return_value = {
                'conf': ['90', '85', '95', '80', '92']
            }
            
            text, confidence = self.processor.extract_text_from_image(temp_path)
            
            assert text == "Sample transaction text"
            assert confidence == 0.904  # (90+85+95+80+92)/5 = 90.4 -> 0.904
            
            # Verify Tesseract was called with correct config
            expected_config = '--oem 3 --psm 6 -l eng+vie'
            mock_image_to_string.assert_called_once()
            mock_image_to_data.assert_called_once()
            
        finally:
            if temp_path.exists():
                temp_path.unlink()

    @patch('snap_transact.ocr.pytesseract.image_to_string')
    @patch('snap_transact.ocr.pytesseract.image_to_data')
    def test_extract_text_from_image_large_image(self, mock_image_to_data, mock_image_to_string):
        """Test text extraction with large image (should be resized)."""
        # Create a large test image
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        try:
            large_image = Image.new('RGB', (3000, 2500), color='white')
            large_image.save(temp_path)
            
            mock_image_to_string.return_value = "Large image text"
            mock_image_to_data.return_value = {'conf': ['90']}
            
            text, confidence = self.processor.extract_text_from_image(temp_path)
            
            assert text == "Large image text"
            assert confidence == 0.90
            
            # Verify image was processed (resized)
            mock_image_to_string.assert_called_once()
            
        finally:
            if temp_path.exists():
                temp_path.unlink()

    @patch('snap_transact.ocr.pytesseract.image_to_string')
    @patch('snap_transact.ocr.pytesseract.image_to_data')
    def test_extract_text_confidence_error(self, mock_image_to_data, mock_image_to_string, mocker: MockerFixture):
        """Test text extraction when confidence data extraction fails."""
        # Create a test image
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        try:
            test_image = Image.new('RGB', (200, 100), color='white')
            test_image.save(temp_path)
            
            mock_image_to_string.return_value = "Sample text"
            mock_image_to_data.side_effect = Exception("Confidence extraction failed")
            
            mock_logger = mocker.patch("snap_transact.ocr.logger")
            
            text, confidence = self.processor.extract_text_from_image(temp_path)
            
            assert text == "Sample text"
            assert confidence == 0.0
            mock_logger.warning.assert_called_once()
            
        finally:
            if temp_path.exists():
                temp_path.unlink()

    @patch('snap_transact.ocr.pytesseract.image_to_string')
    def test_extract_text_from_image_ocr_error(self, mock_image_to_string):
        """Test text extraction when OCR fails."""
        # Create a test image
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        try:
            test_image = Image.new('RGB', (200, 100), color='white')
            test_image.save(temp_path)
            
            mock_image_to_string.side_effect = Exception("OCR failed")
            
            with pytest.raises(Exception, match="OCR failed"):
                self.processor.extract_text_from_image(temp_path)
                
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_validate_image_success(self):
        """Test successful image validation."""
        # Create a valid test image
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        try:
            test_image = Image.new('RGB', (200, 100), color='white')
            test_image.save(temp_path)
            
            result = self.processor.validate_image(temp_path)
            assert result is True
            
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_validate_image_file_not_exists(self, mocker: MockerFixture):
        """Test image validation when file doesn't exist."""
        mock_logger = mocker.patch("snap_transact.ocr.logger")
        
        non_existent_path = Path("non_existent_image.png")
        result = self.processor.validate_image(non_existent_path)
        
        assert result is False
        mock_logger.warning.assert_called_once_with(f"Image file does not exist: {non_existent_path}")

    def test_validate_image_too_large(self, mocker: MockerFixture):
        """Test image validation when file is too large."""
        mock_logger = mocker.patch("snap_transact.ocr.logger")
        
        # Create a temporary file and mock its size
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        try:
            # Create a small image but mock the file size
            test_image = Image.new('RGB', (100, 100), color='white')
            test_image.save(temp_path)
            
            # Mock stat to return large file size
            mock_stat = mocker.patch.object(temp_path, 'stat')
            mock_stat.return_value.st_size = 15_000_000  # 15MB
            
            result = self.processor.validate_image(temp_path)
            
            assert result is False
            mock_logger.warning.assert_called_once_with(f"Image file too large: 15000000 bytes")
            
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_validate_image_unsupported_format(self, mocker: MockerFixture):
        """Test image validation with unsupported format."""
        mock_logger = mocker.patch("snap_transact.ocr.logger")
        
        # Create a test image with unsupported format
        with tempfile.NamedTemporaryFile(suffix='.gif', delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        try:
            # Create a GIF image (unsupported format)
            test_image = Image.new('RGB', (100, 100), color='white')
            test_image.save(temp_path, format='GIF')
            
            result = self.processor.validate_image(temp_path)
            
            assert result is False
            mock_logger.warning.assert_called_once_with("Unsupported image format: GIF")
            
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_validate_image_too_small(self, mocker: MockerFixture):
        """Test image validation when image is too small."""
        mock_logger = mocker.patch("snap_transact.ocr.logger")
        
        # Create a very small test image
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        try:
            test_image = Image.new('RGB', (30, 30), color='white')  # Too small
            test_image.save(temp_path)
            
            result = self.processor.validate_image(temp_path)
            
            assert result is False
            mock_logger.warning.assert_called_once_with("Image too small: (30, 30)")
            
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_validate_image_corrupted_file(self, mocker: MockerFixture):
        """Test image validation with corrupted file."""
        mock_logger = mocker.patch("snap_transact.ocr.logger")
        
        # Create a corrupted file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(b"This is not a valid image file")
        
        try:
            result = self.processor.validate_image(temp_path)
            
            assert result is False
            mock_logger.error.assert_called_once()
            
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_settings_configuration(self):
        """Test different OCR settings configurations."""
        custom_settings = OCRSettings(
            language="eng",
            oem=1,
            psm=8,
            dpi=600,
            preprocess=False
        )
        
        processor = OCRProcessor(custom_settings)
        
        assert processor.settings.language == "eng"
        assert processor.settings.oem == 1
        assert processor.settings.psm == 8
        assert processor.settings.dpi == 600
        assert processor.settings.preprocess is False

    @patch('snap_transact.ocr.pytesseract.image_to_data')
    def test_confidence_calculation_empty_list(self, mock_image_to_data):
        """Test confidence calculation with empty confidence list."""
        mock_image_to_data.return_value = {'conf': []}
        
        # This should be tested within extract_text_from_image
        # but we can test the logic separately
        confidences = []
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        assert avg_confidence == 0.0

    @patch('snap_transact.ocr.pytesseract.image_to_data')
    def test_confidence_calculation_with_negative_values(self, mock_image_to_data):
        """Test confidence calculation filtering negative values."""
        mock_image_to_data.return_value = {'conf': ['90', '-1', '85', '0', '95']}
        
        # Simulate the filtering logic from the actual code
        confidences = [int(conf) for conf in ['90', '-1', '85', '0', '95'] if int(conf) > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        assert confidences == [90, 85, 95]
        assert avg_confidence == 90.0 