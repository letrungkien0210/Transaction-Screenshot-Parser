"""Unit tests for the core module."""

import tempfile
from decimal import Decimal
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest
from pytest_mock import MockerFixture

from snap_transact.core import (
    process_single_image,
    export_transactions_to_csv,
    process_images,
    initialize_sentry,
)
from snap_transact.models import Transaction, ProcessingResult, AppConfig, OCRSettings
from snap_transact.ocr import OCRProcessor
from snap_transact.parser import TransactionParser


class TestCore:
    """Test cases for core module functions."""

    def setup_method(self):
        """Setup test fixtures."""
        self.sample_transaction = Transaction(
            date=datetime(2024, 3, 15),
            amount=Decimal('1500000'),
            description="Transfer to supplier",
            reference="TXN123456789",
            source_file="test_image.png",
            confidence=0.95,
        )

    def test_initialize_sentry_with_dsn(self, mocker: MockerFixture):
        """Test Sentry initialization with DSN."""
        mock_sentry = mocker.patch("snap_transact.core.sentry_sdk.init")
        mock_logger = mocker.patch("snap_transact.core.logger")
        
        dsn = "https://example@sentry.io/123456"
        initialize_sentry(dsn)
        
        mock_sentry.assert_called_once_with(
            dsn=dsn,
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
        )
        mock_logger.info.assert_called_once_with("Sentry initialized for error tracking")

    def test_initialize_sentry_without_dsn(self, mocker: MockerFixture):
        """Test Sentry initialization without DSN."""
        mock_sentry = mocker.patch("snap_transact.core.sentry_sdk.init")
        mock_logger = mocker.patch("snap_transact.core.logger")
        
        initialize_sentry(None)
        
        mock_sentry.assert_not_called()
        mock_logger.info.assert_not_called()

    def test_process_single_image_success(self, mocker: MockerFixture):
        """Test successful processing of a single image."""
        mock_ocr = Mock(spec=OCRProcessor)
        mock_parser = Mock(spec=TransactionParser)
        
        mock_ocr.validate_image.return_value = True
        mock_ocr.extract_text_from_image.return_value = ("Sample transaction text", 0.9)
        mock_parser.parse_transaction_from_text.return_value = [self.sample_transaction]
        
        image_path = Path("test_image.png")
        result = process_single_image(image_path, mock_ocr, mock_parser)
        
        assert len(result) == 1
        assert result[0] == self.sample_transaction
        
        mock_ocr.validate_image.assert_called_once_with(image_path)
        mock_ocr.extract_text_from_image.assert_called_once_with(image_path)
        mock_parser.parse_transaction_from_text.assert_called_once_with(
            text="Sample transaction text",
            source_file=str(image_path),
            confidence=0.9
        )

    def test_process_single_image_invalid_image(self, mocker: MockerFixture):
        """Test processing invalid image."""
        mock_ocr = Mock(spec=OCRProcessor)
        mock_parser = Mock(spec=TransactionParser)
        
        mock_ocr.validate_image.return_value = False
        
        image_path = Path("invalid_image.png")
        result = process_single_image(image_path, mock_ocr, mock_parser)
        
        assert result == []
        mock_ocr.validate_image.assert_called_once_with(image_path)
        mock_ocr.extract_text_from_image.assert_not_called()

    def test_process_single_image_no_text(self, mocker: MockerFixture):
        """Test processing image with no extractable text."""
        mock_ocr = Mock(spec=OCRProcessor)
        mock_parser = Mock(spec=TransactionParser)
        
        mock_ocr.validate_image.return_value = True
        mock_ocr.extract_text_from_image.return_value = ("", 0.0)
        
        image_path = Path("empty_image.png")
        result = process_single_image(image_path, mock_ocr, mock_parser)
        
        assert result == []
        mock_parser.parse_transaction_from_text.assert_not_called()

    def test_process_single_image_exception(self, mocker: MockerFixture):
        """Test processing image with exception."""
        mock_ocr = Mock(spec=OCRProcessor)
        mock_parser = Mock(spec=TransactionParser)
        mock_sentry = mocker.patch("snap_transact.core.sentry_sdk")
        
        mock_ocr.validate_image.return_value = True
        mock_ocr.extract_text_from_image.side_effect = Exception("OCR failed")
        
        # Mock sentry hub
        mock_hub = Mock()
        mock_hub.client = Mock()
        mock_sentry.Hub.current = mock_hub
        
        image_path = Path("error_image.png")
        result = process_single_image(image_path, mock_ocr, mock_parser)
        
        assert result == []
        mock_sentry.capture_exception.assert_called_once()

    def test_export_transactions_to_csv_success(self):
        """Test successful CSV export."""
        transactions = [self.sample_transaction]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
            output_path = Path(temp_file.name)
        
        try:
            export_transactions_to_csv(transactions, output_path)
            
            # Verify file was created
            assert output_path.exists()
            
            # Verify content
            df = pd.read_csv(output_path)
            assert len(df) == 1
            assert df.iloc[0]['date'] == '2024-03-15'
            assert df.iloc[0]['amount'] == '1500000'
            assert df.iloc[0]['description'] == 'Transfer to supplier'
            assert df.iloc[0]['reference'] == 'TXN123456789'
            assert df.iloc[0]['source_file'] == 'test_image.png'
            assert df.iloc[0]['confidence'] == '0.95'
            
        finally:
            # Clean up
            if output_path.exists():
                output_path.unlink()

    def test_export_transactions_to_csv_empty_list(self, mocker: MockerFixture):
        """Test CSV export with empty transaction list."""
        mock_logger = mocker.patch("snap_transact.core.logger")
        
        output_path = Path("empty_output.csv")
        export_transactions_to_csv([], output_path)
        
        mock_logger.warning.assert_called_once_with("No transactions to export")
        assert not output_path.exists()

    def test_export_transactions_to_csv_with_none_values(self):
        """Test CSV export with transactions containing None values."""
        transaction = Transaction(
            date=None,
            amount=None,
            description=None,
            reference=None,
            source_file="test.png",
            confidence=None,
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
            output_path = Path(temp_file.name)
        
        try:
            export_transactions_to_csv([transaction], output_path)
            
            # Verify file was created
            assert output_path.exists()
            
            # Verify content with empty strings for None values
            df = pd.read_csv(output_path)
            assert len(df) == 1
            assert df.iloc[0]['date'] == ''
            assert df.iloc[0]['amount'] == ''
            assert df.iloc[0]['description'] == ''
            assert df.iloc[0]['reference'] == ''
            assert df.iloc[0]['source_file'] == 'test.png'
            assert df.iloc[0]['confidence'] == ''
            
        finally:
            # Clean up
            if output_path.exists():
                output_path.unlink()

    @patch('snap_transact.core.load_config')
    @patch('snap_transact.core.initialize_sentry')
    @patch('snap_transact.core.get_image_files')
    @patch('snap_transact.core.process_single_image')
    @patch('snap_transact.core.export_transactions_to_csv')
    def test_process_images_success(
        self,
        mock_export,
        mock_process_single,
        mock_get_files,
        mock_sentry,
        mock_load_config,
        mocker: MockerFixture
    ):
        """Test successful image processing workflow."""
        # Setup mocks
        mock_config = AppConfig(ocr=OCRSettings())
        mock_load_config.return_value = mock_config
        mock_get_files.return_value = [Path("image1.png"), Path("image2.png")]
        mock_process_single.return_value = [self.sample_transaction]
        
        input_path = Path("input")
        output_path = Path("output.csv")
        
        result = process_images(input_path, output_path)
        
        # Verify calls
        mock_load_config.assert_called_once_with(None)
        mock_sentry.assert_called_once_with(mock_config.sentry_dsn)
        mock_get_files.assert_called_once_with(input_path, mock_config.supported_formats)
        assert mock_process_single.call_count == 2
        mock_export.assert_called_once()
        
        # Verify result
        assert isinstance(result, ProcessingResult)
        assert result.processed_count == 2
        assert result.transaction_count == 2
        assert result.failed_count == 0

    @patch('snap_transact.core.load_config')
    @patch('snap_transact.core.get_image_files')
    def test_process_images_no_files(self, mock_get_files, mock_load_config):
        """Test processing when no image files are found."""
        mock_config = AppConfig(ocr=OCRSettings())
        mock_load_config.return_value = mock_config
        mock_get_files.return_value = []
        
        input_path = Path("empty_input")
        output_path = Path("output.csv")
        
        result = process_images(input_path, output_path)
        
        assert result.processed_count == 0
        assert result.transaction_count == 0

    @patch('snap_transact.core.load_config')
    @patch('snap_transact.core.get_image_files')
    @patch('snap_transact.core.process_single_image')
    def test_process_images_with_failures(
        self,
        mock_process_single,
        mock_get_files,
        mock_load_config,
        mocker: MockerFixture
    ):
        """Test processing with some failed images."""
        mock_config = AppConfig(ocr=OCRSettings())
        mock_load_config.return_value = mock_config
        mock_get_files.return_value = [Path("image1.png"), Path("image2.png")]
        
        # First image succeeds, second fails
        mock_process_single.side_effect = [
            [self.sample_transaction],
            Exception("Processing failed")
        ]
        
        # Mock sentry
        mock_sentry = mocker.patch("snap_transact.core.sentry_sdk")
        mock_hub = Mock()
        mock_hub.client = Mock()
        mock_sentry.Hub.current = mock_hub
        
        input_path = Path("input")
        output_path = Path("output.csv")
        
        result = process_images(input_path, output_path)
        
        assert result.processed_count == 1
        assert result.transaction_count == 1
        assert result.failed_count == 1 