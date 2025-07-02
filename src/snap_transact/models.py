"""Pydantic models for transaction data and configuration."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Transaction(BaseModel):
    """Transaction data model."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    date: Optional[datetime] = Field(None, description="Transaction date")
    amount: Optional[Decimal] = Field(None, description="Transaction amount")
    description: Optional[str] = Field(None, description="Transaction description")
    account: Optional[str] = Field(None, description="Account information")
    category: Optional[str] = Field(None, description="Transaction category")
    reference: Optional[str] = Field(None, description="Reference number")
    balance: Optional[Decimal] = Field(None, description="Account balance after transaction")
    source_file: Optional[str] = Field(None, description="Source image file path")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="OCR confidence score")


class ProcessingResult(BaseModel):
    """Result of image processing operation."""

    processed_count: int = Field(description="Number of images processed")
    transaction_count: int = Field(description="Number of transactions extracted")
    failed_count: int = Field(default=0, description="Number of failed processing attempts")
    transactions: List[Transaction] = Field(default_factory=list, description="List of extracted transactions")


class OCRSettings(BaseModel):
    """OCR configuration settings."""

    language: str = Field(default="eng+vie", description="Tesseract language codes")
    oem: int = Field(default=3, description="OCR Engine Mode")
    psm: int = Field(default=6, description="Page Segmentation Mode")
    dpi: int = Field(default=300, description="DPI for image processing")
    preprocess: bool = Field(default=True, description="Enable image preprocessing")


class AppConfig(BaseModel):
    """Application configuration."""

    model_config = ConfigDict(env_prefix="SNAP_TRANSACT_")

    ocr: OCRSettings = Field(default_factory=OCRSettings)
    output_format: str = Field(default="csv", description="Output format")
    supported_formats: List[str] = Field(
        default_factory=lambda: [".png", ".jpg", ".jpeg", ".tiff", ".bmp"],
        description="Supported image formats"
    )
    max_image_size: int = Field(default=10_000_000, description="Maximum image size in bytes")
    sentry_dsn: Optional[str] = Field(None, description="Sentry DSN for error tracking")
    log_level: str = Field(default="INFO", description="Logging level") 