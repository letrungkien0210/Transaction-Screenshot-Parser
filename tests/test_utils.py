"""Unit tests for the utils module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest
import yaml
from pytest_mock import MockerFixture

from snap_transact.utils import load_config, get_image_files
from snap_transact.models import AppConfig, OCRSettings


class TestLoadConfig:
    """Test cases for load_config function."""

    def test_load_config_no_file(self, mocker: MockerFixture):
        """Test loading config without config file."""
        mock_logger = mocker.patch("snap_transact.utils.logger")
        
        config = load_config()
        
        assert isinstance(config, AppConfig)
        assert config.ocr.language == "eng+vie"  # Default value
        assert config.output_format == "csv"      # Default value
        mock_logger.debug.assert_called_once_with("Configuration loaded successfully")

    def test_load_config_with_valid_file(self, mocker: MockerFixture):
        """Test loading config from valid YAML file."""
        mock_logger = mocker.patch("snap_transact.utils.logger")
        
        # Create a temporary config file
        config_data = {
            "ocr": {
                "language": "eng",
                "oem": 1,
                "psm": 8,
                "dpi": 600,
                "preprocess": False
            },
            "output_format": "json",
            "max_image_size": 5000000,
            "log_level": "DEBUG"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.dump(config_data, temp_file)
            temp_path = Path(temp_file.name)
        
        try:
            config = load_config(temp_path)
            
            assert isinstance(config, AppConfig)
            assert config.ocr.language == "eng"
            assert config.ocr.oem == 1
            assert config.ocr.psm == 8
            assert config.ocr.dpi == 600
            assert config.ocr.preprocess is False
            assert config.output_format == "json"
            assert config.max_image_size == 5000000
            assert config.log_level == "DEBUG"
            
            mock_logger.info.assert_called_once_with(f"Loaded configuration from {temp_path}")
            mock_logger.debug.assert_called_once_with("Configuration loaded successfully")
            
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_load_config_file_not_exists(self, mocker: MockerFixture):
        """Test loading config when file doesn't exist."""
        mock_logger = mocker.patch("snap_transact.utils.logger")
        
        non_existent_path = Path("non_existent_config.yaml")
        config = load_config(non_existent_path)
        
        assert isinstance(config, AppConfig)
        # Should use default values
        assert config.ocr.language == "eng+vie"
        mock_logger.debug.assert_called_once_with("Configuration loaded successfully")

    def test_load_config_invalid_yaml(self, mocker: MockerFixture):
        """Test loading config with invalid YAML content."""
        mock_logger = mocker.patch("snap_transact.utils.logger")
        
        # Create a file with invalid YAML
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            temp_file.write("invalid: yaml: content: [unclosed")
            temp_path = Path(temp_file.name)
        
        try:
            config = load_config(temp_path)
            
            assert isinstance(config, AppConfig)
            # Should use default values
            assert config.ocr.language == "eng+vie"
            
            mock_logger.warning.assert_called_once()
            mock_logger.info.assert_called_once_with("Using default configuration")
            
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_load_config_empty_yaml(self, mocker: MockerFixture):
        """Test loading config with empty YAML file."""
        mock_logger = mocker.patch("snap_transact.utils.logger")
        
        # Create an empty YAML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            temp_file.write("")
            temp_path = Path(temp_file.name)
        
        try:
            config = load_config(temp_path)
            
            assert isinstance(config, AppConfig)
            # Should use default values
            assert config.ocr.language == "eng+vie"
            
            mock_logger.info.assert_called_once_with(f"Loaded configuration from {temp_path}")
            mock_logger.debug.assert_called_once_with("Configuration loaded successfully")
            
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_load_config_validation_error(self, mocker: MockerFixture):
        """Test loading config with validation error."""
        mock_logger = mocker.patch("snap_transact.utils.logger")
        
        # Create config with invalid data
        config_data = {
            "ocr": {
                "language": "eng",
                "oem": "invalid_oem",  # Should be int
                "psm": -1,             # Should be positive
            },
            "max_image_size": "invalid_size"  # Should be int
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.dump(config_data, temp_file)
            temp_path = Path(temp_file.name)
        
        try:
            config = load_config(temp_path)
            
            assert isinstance(config, AppConfig)
            # Should use default values due to validation error
            assert config.ocr.language == "eng+vie"
            
            mock_logger.error.assert_called_once()
            mock_logger.info.assert_called_once_with("Using default configuration")
            
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_load_config_with_environment_variables(self, mocker: MockerFixture):
        """Test loading config with environment variables."""
        mock_logger = mocker.patch("snap_transact.utils.logger")
        
        # Mock environment variables
        env_vars = {
            "SNAP_TRANSACT_OCR__LANGUAGE": "vie",
            "SNAP_TRANSACT_LOG_LEVEL": "WARNING",
            "SNAP_TRANSACT_SENTRY_DSN": "https://test@sentry.io/123"
        }
        
        with patch.dict(os.environ, env_vars):
            config = load_config()
            
            assert isinstance(config, AppConfig)
            assert config.ocr.language == "vie"
            assert config.log_level == "WARNING"
            assert config.sentry_dsn == "https://test@sentry.io/123"

    def test_load_config_file_permission_error(self, mocker: MockerFixture):
        """Test loading config when file has permission issues."""
        mock_logger = mocker.patch("snap_transact.utils.logger")
        
        # Create a file and mock open to raise PermissionError
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        try:
            with patch('builtins.open', side_effect=PermissionError("Permission denied")):
                config = load_config(temp_path)
                
                assert isinstance(config, AppConfig)
                # Should use default values
                assert config.ocr.language == "eng+vie"
                
                mock_logger.warning.assert_called_once()
                mock_logger.info.assert_called_once_with("Using default configuration")
                
        finally:
            if temp_path.exists():
                temp_path.unlink()


class TestGetImageFiles:
    """Test cases for get_image_files function."""

    def test_get_image_files_single_file_supported(self, mocker: MockerFixture):
        """Test getting image files with single supported file."""
        mock_logger = mocker.patch("snap_transact.utils.logger")
        
        # Create a test image file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        try:
            supported_formats = ['.png', '.jpg', '.jpeg']
            result = get_image_files(temp_path, supported_formats)
            
            assert len(result) == 1
            assert result[0] == temp_path
            mock_logger.debug.assert_called_once_with(f"Single image file: {temp_path}")
            
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_get_image_files_single_file_unsupported(self, mocker: MockerFixture):
        """Test getting image files with single unsupported file."""
        mock_logger = mocker.patch("snap_transact.utils.logger")
        
        # Create a test file with unsupported extension
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        try:
            supported_formats = ['.png', '.jpg', '.jpeg']
            result = get_image_files(temp_path, supported_formats)
            
            assert len(result) == 0
            mock_logger.warning.assert_called_once_with(f"Unsupported file format: {temp_path.suffix}")
            
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_get_image_files_directory_with_images(self, mocker: MockerFixture):
        """Test getting image files from directory with multiple images."""
        mock_logger = mocker.patch("snap_transact.utils.logger")
        
        # Create a temporary directory with image files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test image files
            image_files = [
                temp_path / "image1.png",
                temp_path / "image2.jpg",
                temp_path / "image3.jpeg",
                temp_path / "document.txt",  # Non-image file
            ]
            
            for file_path in image_files:
                file_path.touch()
            
            supported_formats = ['.png', '.jpg', '.jpeg']
            result = get_image_files(temp_path, supported_formats)
            
            # Should only include image files, sorted
            assert len(result) == 3
            assert all(f.suffix.lower() in supported_formats for f in result)
            
            # Check if results are sorted
            assert result == sorted(result)
            
            mock_logger.debug.assert_called_once_with(f"Found 3 image files in directory: {temp_path}")

    def test_get_image_files_empty_directory(self, mocker: MockerFixture):
        """Test getting image files from empty directory."""
        mock_logger = mocker.patch("snap_transact.utils.logger")
        
        # Create an empty temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            supported_formats = ['.png', '.jpg', '.jpeg']
            result = get_image_files(temp_path, supported_formats)
            
            assert len(result) == 0
            mock_logger.debug.assert_called_once_with(f"Found 0 image files in directory: {temp_path}")

    def test_get_image_files_directory_no_supported_files(self, mocker: MockerFixture):
        """Test getting image files from directory with no supported files."""
        mock_logger = mocker.patch("snap_transact.utils.logger")
        
        # Create a temporary directory with non-image files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test non-image files
            non_image_files = [
                temp_path / "document.txt",
                temp_path / "data.csv",
                temp_path / "script.py",
            ]
            
            for file_path in non_image_files:
                file_path.touch()
            
            supported_formats = ['.png', '.jpg', '.jpeg']
            result = get_image_files(temp_path, supported_formats)
            
            assert len(result) == 0
            mock_logger.debug.assert_called_once_with(f"Found 0 image files in directory: {temp_path}")

    def test_get_image_files_non_existent_path(self, mocker: MockerFixture):
        """Test getting image files from non-existent path."""
        mock_logger = mocker.patch("snap_transact.utils.logger")
        
        non_existent_path = Path("non_existent_directory")
        supported_formats = ['.png', '.jpg', '.jpeg']
        
        result = get_image_files(non_existent_path, supported_formats)
        
        assert len(result) == 0
        mock_logger.error.assert_called_once_with(f"Input path does not exist or is not accessible: {non_existent_path}")

    def test_get_image_files_case_insensitive(self, mocker: MockerFixture):
        """Test getting image files with case-insensitive extension matching."""
        mock_logger = mocker.patch("snap_transact.utils.logger")
        
        # Create a temporary directory with image files having different case extensions
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test image files with different case extensions
            image_files = [
                temp_path / "image1.PNG",
                temp_path / "image2.JPG",
                temp_path / "image3.jpeg",
                temp_path / "image4.Png",
            ]
            
            for file_path in image_files:
                file_path.touch()
            
            supported_formats = ['.png', '.jpg', '.jpeg']
            result = get_image_files(temp_path, supported_formats)
            
            # Should include all image files regardless of case
            assert len(result) == 4
            assert all(f.suffix.lower() in supported_formats for f in result)

    def test_get_image_files_sorting(self, mocker: MockerFixture):
        """Test that image files are returned in sorted order."""
        mock_logger = mocker.patch("snap_transact.utils.logger")
        
        # Create a temporary directory with image files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test image files in non-alphabetical order
            image_files = [
                temp_path / "z_image.png",
                temp_path / "a_image.jpg",
                temp_path / "m_image.jpeg",
                temp_path / "c_image.png",
            ]
            
            for file_path in image_files:
                file_path.touch()
            
            supported_formats = ['.png', '.jpg', '.jpeg']
            result = get_image_files(temp_path, supported_formats)
            
            # Should be sorted alphabetically
            assert len(result) == 4
            assert result == sorted(result)
            assert result[0].name == "a_image.jpg"
            assert result[1].name == "c_image.png"
            assert result[2].name == "m_image.jpeg"
            assert result[3].name == "z_image.png"

    def test_get_image_files_with_subdirectories(self, mocker: MockerFixture):
        """Test getting image files from directory with subdirectories."""
        mock_logger = mocker.patch("snap_transact.utils.logger")
        
        # Create a temporary directory with subdirectories
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create subdirectory
            subdir = temp_path / "subdir"
            subdir.mkdir()
            
            # Create files in main directory and subdirectory
            main_file = temp_path / "main.png"
            sub_file = subdir / "sub.jpg"
            main_file.touch()
            sub_file.touch()
            
            supported_formats = ['.png', '.jpg', '.jpeg']
            result = get_image_files(temp_path, supported_formats)
            
            # Should only include files from main directory, not subdirectories
            assert len(result) == 1
            assert result[0] == main_file 