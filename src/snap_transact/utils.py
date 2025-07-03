"""Helper functions and utilities."""

import os
from pathlib import Path
from typing import List, Optional

import yaml
from loguru import logger
from pydantic import ValidationError

from snap_transact.models import AppConfig


def load_config(config_path: Optional[Path] = None) -> AppConfig:
    """Load application configuration from file or environment variables.
    
    Args:
        config_path: Optional path to YAML configuration file
        
    Returns:
        AppConfig object with loaded configuration
    """
    config_data = {}
    
    # Load from YAML file if provided
    if config_path and config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f) or {}
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.warning(f"Failed to load config file {config_path}: {e}")
            logger.info("Using default configuration")
    
    # Create configuration object (will also load from environment variables)
    try:
        config = AppConfig(**config_data)
        logger.debug("Configuration loaded successfully")
        return config
    except ValidationError as e:
        logger.error(f"Configuration validation failed: {e}")
        logger.info("Using default configuration")
        return AppConfig()


def get_image_files(input_path: Path, supported_formats: List[str]) -> List[Path]:
    """Get list of supported image files from input path.
    
    Args:
        input_path: Path to file or directory
        supported_formats: List of supported file extensions
        
    Returns:
        List of image file paths
    """
    image_files: List[Path] = []
    
    if input_path.is_file():
        # Single file
        if input_path.suffix.lower() in supported_formats:
            image_files.append(input_path)
            logger.debug(f"Single image file: {input_path}")
        else:
            logger.warning(f"Unsupported file format: {input_path.suffix}")
    
    elif input_path.is_dir():
        # Directory of files
        for file_path in input_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in supported_formats:
                image_files.append(file_path)
        
        logger.debug(f"Found {len(image_files)} image files in directory: {input_path}")
    
    else:
        logger.error(f"Input path does not exist or is not accessible: {input_path}")
    
    # Sort files for consistent processing order
    image_files.sort()
    
    return image_files 