"""Integration tests for the SnapTransact CLI."""

import tempfile
from pathlib import Path
from unittest.mock import patch, Mock

import pandas as pd
import pytest
from typer.testing import CliRunner
from pytest_mock import MockerFixture

from snap_transact.main import app
from snap_transact.models import Transaction
from decimal import Decimal
from datetime import datetime


class TestIntegration:
    """Integration tests for the full application workflow."""

    def setup_method(self):
        """Setup test fixtures."""
        self.runner = CliRunner()
        self.sample_transaction = Transaction(
            date=datetime(2024, 3, 15),
            amount=Decimal('1500000'),
            description="Transfer to supplier",
            reference="TXN123456789",
            source_file="test_image.png",
            confidence=0.95,
        )

    def test_cli_help_command(self):
        """Test CLI help command."""
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "SnapTransact CLI" in result.output
        assert "Extract transaction data from screenshots" in result.output

    def test_cli_version_command(self):
        """Test CLI version command."""
        result = self.runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "SnapTransact CLI" in result.output

    def test_process_command_help(self):
        """Test process command help."""
        result = self.runner.invoke(app, ["process", "--help"])
        assert result.exit_code == 0
        assert "Process images and extract transaction data" in result.output

    @patch('snap_transact.main.process_images')
    def test_process_command_single_file(self, mock_process_images):
        """Test process command with single file."""
        # Create a temporary image file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(b"fake image data")
        
        try:
            # Mock successful processing
            from snap_transact.models import ProcessingResult
            mock_process_images.return_value = ProcessingResult(
                processed_count=1,
                transaction_count=1,
                failed_count=0,
                transactions=[self.sample_transaction]
            )
            
            # Create temporary output file
            with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as output_file:
                output_path = Path(output_file.name)
            
            try:
                result = self.runner.invoke(app, [
                    "process",
                    str(temp_path),
                    "--output", str(output_path)
                ])
                
                assert result.exit_code == 0
                mock_process_images.assert_called_once_with(
                    temp_path, output_path, None
                )
                
            finally:
                if output_path.exists():
                    output_path.unlink()
                    
        finally:
            if temp_path.exists():
                temp_path.unlink()

    @patch('snap_transact.main.process_images')
    def test_process_command_with_config(self, mock_process_images):
        """Test process command with configuration file."""
        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(b"fake image data")
        
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as config_file:
            config_path = Path(config_file.name)
            config_file.write(b"ocr:\n  language: eng\n")
        
        try:
            # Mock successful processing
            from snap_transact.models import ProcessingResult
            mock_process_images.return_value = ProcessingResult(
                processed_count=1,
                transaction_count=1,
                failed_count=0
            )
            
            result = self.runner.invoke(app, [
                "process",
                str(temp_path),
                "--config", str(config_path)
            ])
            
            assert result.exit_code == 0
            mock_process_images.assert_called_once()
            
        finally:
            if temp_path.exists():
                temp_path.unlink()
            if config_path.exists():
                config_path.unlink()

    @patch('snap_transact.main.process_images')
    def test_process_command_verbose(self, mock_process_images):
        """Test process command with verbose logging."""
        # Create a temporary image file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(b"fake image data")
        
        try:
            # Mock successful processing
            from snap_transact.models import ProcessingResult
            mock_process_images.return_value = ProcessingResult(
                processed_count=1,
                transaction_count=1,
                failed_count=0
            )
            
            result = self.runner.invoke(app, [
                "process",
                str(temp_path),
                "--verbose"
            ])
            
            assert result.exit_code == 0
            mock_process_images.assert_called_once()
            
        finally:
            if temp_path.exists():
                temp_path.unlink()

    @patch('snap_transact.main.process_images')
    def test_process_command_failure(self, mock_process_images):
        """Test process command when processing fails."""
        # Create a temporary image file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(b"fake image data")
        
        try:
            # Mock processing failure
            mock_process_images.side_effect = Exception("Processing failed")
            
            result = self.runner.invoke(app, [
                "process",
                str(temp_path)
            ])
            
            assert result.exit_code == 1
            assert "Failed to process images" in result.output
            
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_process_command_nonexistent_file(self):
        """Test process command with non-existent file."""
        result = self.runner.invoke(app, [
            "process",
            "nonexistent_file.png"
        ])
        
        assert result.exit_code != 0
        assert "does not exist" in result.output

    @patch('snap_transact.core.OCRProcessor')
    @patch('snap_transact.core.TransactionParser')
    @patch('snap_transact.core.load_config')
    @patch('snap_transact.core.get_image_files')
    def test_end_to_end_workflow(
        self,
        mock_get_files,
        mock_load_config,
        mock_parser_class,
        mock_ocr_class
    ):
        """Test end-to-end workflow from image to CSV."""
        # Setup mocks
        from snap_transact.models import AppConfig, OCRSettings
        mock_config = AppConfig(ocr=OCRSettings())
        mock_load_config.return_value = mock_config
        
        # Create temporary image file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(b"fake image data")
        
        mock_get_files.return_value = [temp_path]
        
        # Mock OCR processor
        mock_ocr = Mock()
        mock_ocr.validate_image.return_value = True
        mock_ocr.extract_text_from_image.return_value = ("Transaction text", 0.9)
        mock_ocr_class.return_value = mock_ocr
        
        # Mock parser
        mock_parser = Mock()
        mock_parser.parse_transaction_from_text.return_value = [self.sample_transaction]
        mock_parser_class.return_value = mock_parser
        
        try:
            # Create temporary output file
            with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as output_file:
                output_path = Path(output_file.name)
            
            try:
                result = self.runner.invoke(app, [
                    "process",
                    str(temp_path),
                    "--output", str(output_path)
                ])
                
                assert result.exit_code == 0
                assert "Successfully processed 1 images" in result.output
                assert "Extracted 1 transactions" in result.output
                
                # Verify CSV was created and contains expected data
                assert output_path.exists()
                df = pd.read_csv(output_path)
                assert len(df) == 1
                assert df.iloc[0]['date'] == '2024-03-15'
                assert df.iloc[0]['amount'] == '1500000'
                assert df.iloc[0]['description'] == 'Transfer to supplier'
                
            finally:
                if output_path.exists():
                    output_path.unlink()
                    
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_cli_error_handling(self):
        """Test CLI error handling with invalid arguments."""
        # Test with invalid config file
        result = self.runner.invoke(app, [
            "process",
            "test.png",
            "--config", "nonexistent_config.yaml"
        ])
        
        assert result.exit_code != 0

    @patch('snap_transact.main.process_images')
    def test_process_command_default_output(self, mock_process_images):
        """Test process command with default output file."""
        # Create a temporary image file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(b"fake image data")
        
        try:
            # Mock successful processing
            from snap_transact.models import ProcessingResult
            mock_process_images.return_value = ProcessingResult(
                processed_count=1,
                transaction_count=1,
                failed_count=0
            )
            
            result = self.runner.invoke(app, [
                "process",
                str(temp_path)
            ])
            
            assert result.exit_code == 0
            
            # Verify default output path was used
            args, kwargs = mock_process_images.call_args
            assert args[1] == Path("transactions.csv")  # Default output path
            
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_callback_version_handling(self):
        """Test version callback handling."""
        # Test that version callback exits cleanly
        result = self.runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "SnapTransact CLI" in result.output

    def test_callback_verbose_logging(self):
        """Test verbose logging configuration."""
        # Create a temporary image file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(b"fake image data")
        
        try:
            with patch('snap_transact.main.process_images') as mock_process:
                from snap_transact.models import ProcessingResult
                mock_process.return_value = ProcessingResult(
                    processed_count=0,
                    transaction_count=0,
                    failed_count=0
                )
                
                result = self.runner.invoke(app, [
                    "--verbose",
                    "process",
                    str(temp_path)
                ])
                
                assert result.exit_code == 0
                
        finally:
            if temp_path.exists():
                temp_path.unlink() 