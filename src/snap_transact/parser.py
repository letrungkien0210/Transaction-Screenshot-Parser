"""Text parsing logic to extract transaction data from OCR text."""

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Pattern

from loguru import logger

from snap_transact.models import Transaction


class TransactionParser:
    """Parses OCR text to extract transaction information."""

    def __init__(self) -> None:
        """Initialize parser with regex patterns."""
        self.date_patterns = self._compile_date_patterns()
        self.amount_patterns = self._compile_amount_patterns()
        self.reference_patterns = self._compile_reference_patterns()

    def _compile_date_patterns(self) -> List[Pattern[str]]:
        """Compile regex patterns for date extraction."""
        patterns = [
            # DD/MM/YYYY or DD-MM-YYYY
            re.compile(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', re.IGNORECASE),
            # DD/MM/YY or DD-MM-YY
            re.compile(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2})', re.IGNORECASE),
            # YYYY-MM-DD
            re.compile(r'(\d{4})-(\d{1,2})-(\d{1,2})', re.IGNORECASE),
            # DD.MM.YYYY
            re.compile(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', re.IGNORECASE),
            # Vietnamese date format: ngày DD tháng MM năm YYYY
            re.compile(r'ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})', re.IGNORECASE),
        ]
        logger.debug(f"Compiled {len(patterns)} date patterns")
        return patterns

    def _compile_amount_patterns(self) -> List[Pattern[str]]:
        """Compile regex patterns for amount extraction."""
        patterns = [
            # Vietnamese currency: 1.000.000 VND or 1,000,000 VND
            re.compile(r'([\d.,]+)\s*(?:VND|VNĐ|đ)', re.IGNORECASE),
            # Amount with currency symbol: $1,000.00
            re.compile(r'[\$€£¥]\s*([\d.,]+)', re.IGNORECASE),
            # Amount followed by currency: 1000.00 USD
            re.compile(r'([\d.,]+)\s*(?:USD|EUR|GBP|JPY)', re.IGNORECASE),
            # Vietnamese format: -1.000.000 or +1.000.000
            re.compile(r'[+-]?\s*([\d.,]+)', re.IGNORECASE),
        ]
        logger.debug(f"Compiled {len(patterns)} amount patterns")
        return patterns

    def _compile_reference_patterns(self) -> List[Pattern[str]]:
        """Compile regex patterns for reference number extraction."""
        patterns = [
            # Transaction ID, Reference, etc.
            re.compile(r'(?:ref|reference|trans|transaction|id|mã gd)[\s:]*([A-Z0-9]+)', re.IGNORECASE),
            # ATM transaction codes
            re.compile(r'ATM[\s:]*([A-Z0-9]+)', re.IGNORECASE),
            # FT (Fund Transfer) codes
            re.compile(r'FT[\s:]*([A-Z0-9]+)', re.IGNORECASE),
        ]
        logger.debug(f"Compiled {len(patterns)} reference patterns")
        return patterns

    def parse_date(self, text: str) -> Optional[datetime]:
        """Extract date from text.
        
        Args:
            text: Input text to parse
            
        Returns:
            Parsed datetime object or None if not found
        """
        for pattern in self.date_patterns:
            match = pattern.search(text)
            if match:
                try:
                    groups = match.groups()
                    if len(groups) == 3:
                        # Handle different date formats
                        if len(groups[0]) == 4:  # YYYY-MM-DD format
                            year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                        elif "tháng" in match.group(0).lower():  # Vietnamese format
                            day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                        else:  # DD/MM/YYYY or DD-MM-YY format
                            day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                            if year < 100:  # Handle 2-digit years
                                year += 2000 if year < 50 else 1900
                        
                        date_obj = datetime(year, month, day)
                        logger.debug(f"Parsed date: {date_obj.strftime('%Y-%m-%d')}")
                        return date_obj
                except (ValueError, IndexError) as e:
                    logger.debug(f"Failed to parse date from {match.group(0)}: {e}")
                    continue
        
        logger.debug("No date found in text")
        return None

    def parse_amount(self, text: str) -> Optional[Decimal]:
        """Extract amount from text.
        
        Args:
            text: Input text to parse
            
        Returns:
            Parsed Decimal amount or None if not found
        """
        for pattern in self.amount_patterns:
            matches = pattern.findall(text)
            for match in matches:
                try:
                    # Clean the amount string
                    amount_str = str(match).replace(',', '').replace('.', '')
                    
                    # Handle Vietnamese format (dots as thousand separators)
                    if '.' in str(match) and str(match).count('.') > 1:
                        # Remove thousand separators (dots)
                        amount_str = str(match).replace('.', '', str(match).count('.') - 1)
                        amount_str = amount_str.replace('.', '')
                    elif ',' in str(match):
                        # Handle comma as decimal separator or thousand separator
                        parts = str(match).split(',')
                        if len(parts) == 2 and len(parts[1]) <= 2:
                            # Likely decimal separator
                            amount_str = parts[0].replace('.', '') + '.' + parts[1]
                        else:
                            # Likely thousand separator
                            amount_str = str(match).replace(',', '')
                    
                    amount = Decimal(amount_str)
                    if amount > 0:  # Only return positive amounts
                        logger.debug(f"Parsed amount: {amount}")
                        return amount
                        
                except (InvalidOperation, ValueError) as e:
                    logger.debug(f"Failed to parse amount from {match}: {e}")
                    continue
        
        logger.debug("No valid amount found in text")
        return None

    def parse_reference(self, text: str) -> Optional[str]:
        """Extract reference number from text.
        
        Args:
            text: Input text to parse
            
        Returns:
            Reference number or None if not found
        """
        for pattern in self.reference_patterns:
            match = pattern.search(text)
            if match:
                reference = match.group(1).strip()
                if len(reference) >= 4:  # Minimum length for valid reference
                    logger.debug(f"Parsed reference: {reference}")
                    return reference
        
        logger.debug("No reference found in text")
        return None

    def extract_description(self, text: str) -> Optional[str]:
        """Extract transaction description from text.
        
        Args:
            text: Input text to parse
            
        Returns:
            Transaction description or None if not found
        """
        # Common Vietnamese transaction description patterns
        desc_patterns = [
            r'(?:mo ta|mô tả|noi dung|nội dung)[\s:]*([^\n]+)',
            r'(?:description|desc)[\s:]*([^\n]+)',
            r'(?:remark|note)[\s:]*([^\n]+)',
        ]
        
        for pattern_str in desc_patterns:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            match = pattern.search(text)
            if match:
                description = match.group(1).strip()
                if len(description) > 3:
                    logger.debug(f"Extracted description: {description[:50]}...")
                    return description
        
        # Fallback: try to extract meaningful text lines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        for line in lines:
            # Skip lines that look like dates, amounts, or references
            if not any([
                re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', line),
                re.search(r'[\d.,]+\s*(?:VND|VNĐ|đ|\$)', line),
                re.search(r'^[A-Z0-9]{6,}$', line),
                len(line) < 5,
            ]):
                logger.debug(f"Using line as description: {line[:50]}...")
                return line
        
        logger.debug("No description found in text")
        return None

    def parse_transaction_from_text(self, text: str, source_file: str, confidence: float) -> List[Transaction]:
        """Parse transaction data from OCR text.
        
        Args:
            text: OCR extracted text
            source_file: Source image file path
            confidence: OCR confidence score
            
        Returns:
            List of Transaction objects (may be empty if no transaction found)
        """
        logger.debug(f"Parsing transaction from text (confidence: {confidence:.2f})")
        
        if not text or len(text.strip()) < 10:
            logger.warning("Text too short to contain transaction data")
            return []
        
        # Extract transaction components
        date = self.parse_date(text)
        amount = self.parse_amount(text)
        reference = self.parse_reference(text)
        description = self.extract_description(text)
        
        # Create transaction if we have at least amount or meaningful description
        if amount or (description and len(description) > 5):
            transaction = Transaction(
                date=date,
                amount=amount,
                description=description,
                reference=reference,
                source_file=source_file,
                confidence=confidence,
            )
            
            logger.info(f"Parsed transaction: amount={amount}, date={date}, ref={reference}")
            return [transaction]
        
        logger.warning("Could not extract sufficient transaction data from text")
        return [] 