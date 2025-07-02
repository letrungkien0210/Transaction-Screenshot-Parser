"""Main orchestration logic for processing images and extracting transactions."""

from pathlib import Path
from typing import List, Optional

import pandas as pd
import sentry_sdk
from loguru import logger

from snap_transact.models import AppConfig, ProcessingResult, Transaction
from snap_transact.ocr import OCRProcessor
from snap_transact.parser import TransactionParser
from snap_transact.utils import load_config, get_image_files


def initialize_sentry(dsn: Optional[str]) -> None:
    """Initialize Sentry for error tracking."""
    if dsn:
        sentry_sdk.init(
            dsn=dsn,
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
        )
        logger.info("Sentry initialized for error tracking")


def process_single_image(
    image_path: Path,
    ocr_processor: OCRProcessor,
    parser: TransactionParser,
) -> List[Transaction]:
    """Process a single image and extract transactions.
    
    Args:
        image_path: Path to the image file
        ocr_processor: OCR processor instance
        parser: Transaction parser instance
        
    Returns:
        List of extracted transactions
    """
    logger.info(f"Processing image: {image_path.name}")
    
    try:
        # Validate image
        if not ocr_processor.validate_image(image_path):
            logger.warning(f"Skipping invalid image: {image_path}")
            return []
        
        # Extract text from image
        text, confidence = ocr_processor.extract_text_from_image(image_path)
        
        if not text or len(text.strip()) < 5:
            logger.warning(f"No meaningful text extracted from {image_path}")
            return []
        
        logger.debug(f"Extracted text ({len(text)} chars, confidence: {confidence:.2f})")
        
        # Parse transactions from text
        transactions = parser.parse_transaction_from_text(
            text=text,
            source_file=str(image_path),
            confidence=confidence
        )
        
        logger.info(f"Extracted {len(transactions)} transactions from {image_path.name}")
        return transactions
        
    except Exception as e:
        logger.error(f"Failed to process image {image_path}: {e}")
        if sentry_sdk.Hub.current.client:
            sentry_sdk.capture_exception(e)
        return []


def export_transactions_to_csv(transactions: List[Transaction], output_path: Path) -> None:
    """Export transactions to CSV file.
    
    Args:
        transactions: List of transactions to export
        output_path: Output CSV file path
    """
    if not transactions:
        logger.warning("No transactions to export")
        return
    
    # Convert transactions to DataFrame
    data = []
    for transaction in transactions:
        data.append({
            'date': transaction.date.strftime('%Y-%m-%d') if transaction.date else '',
            'amount': str(transaction.amount) if transaction.amount else '',
            'description': transaction.description or '',
            'account': transaction.account or '',
            'category': transaction.category or '',
            'reference': transaction.reference or '',
            'balance': str(transaction.balance) if transaction.balance else '',
            'source_file': transaction.source_file or '',
            'confidence': f"{transaction.confidence:.2f}" if transaction.confidence else '',
        })
    
    df = pd.DataFrame(data)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Export to CSV
    df.to_csv(output_path, index=False, encoding='utf-8')
    logger.info(f"Exported {len(transactions)} transactions to {output_path}")


def process_images(
    input_path: Path,
    output_path: Path,
    config_path: Optional[Path] = None,
) -> ProcessingResult:
    """Main function to process images and extract transaction data.
    
    Args:
        input_path: Path to image file or directory
        output_path: Output CSV file path
        config_path: Optional configuration file path
        
    Returns:
        ProcessingResult with processing statistics
    """
    logger.info("Starting transaction extraction process")
    
    # Load configuration
    config = load_config(config_path)
    
    # Initialize Sentry
    initialize_sentry(config.sentry_dsn)
    
    # Initialize processors
    ocr_processor = OCRProcessor(config.ocr)
    parser = TransactionParser()
    
    # Get list of image files to process
    image_files = get_image_files(input_path, config.supported_formats)
    
    if not image_files:
        logger.warning(f"No supported image files found in {input_path}")
        return ProcessingResult(processed_count=0, transaction_count=0)
    
    logger.info(f"Found {len(image_files)} image files to process")
    
    # Process all images
    all_transactions: List[Transaction] = []
    processed_count = 0
    failed_count = 0
    
    for image_path in image_files:
        try:
            transactions = process_single_image(image_path, ocr_processor, parser)
            all_transactions.extend(transactions)
            processed_count += 1
            logger.debug(f"Progress: {processed_count}/{len(image_files)} images processed")
        except Exception as e:
            logger.error(f"Failed to process {image_path}: {e}")
            failed_count += 1
            if sentry_sdk.Hub.current.client:
                sentry_sdk.capture_exception(e)
    
    # Export results
    if all_transactions:
        export_transactions_to_csv(all_transactions, output_path)
    else:
        logger.warning("No transactions extracted from any images")
    
    # Return processing result
    result = ProcessingResult(
        processed_count=processed_count,
        transaction_count=len(all_transactions),
        failed_count=failed_count,
        transactions=all_transactions,
    )
    
    logger.info(f"Processing complete: {result.processed_count} images processed, "
                f"{result.transaction_count} transactions extracted, "
                f"{result.failed_count} failures")
    
    return result 