"""Unit tests for the transaction parser module."""

from decimal import Decimal
from datetime import datetime

import pytest
from pytest_mock import MockerFixture

from snap_transact.parser import TransactionParser
from snap_transact.models import Transaction


class TestTransactionParser:
    """Test cases for TransactionParser class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.parser = TransactionParser()

    def test_parse_date_dd_mm_yyyy_format(self):
        """Test parsing date in DD/MM/YYYY format."""
        text = "Date: 15/03/2024 Transaction details"
        result = self.parser.parse_date(text)
        
        assert result is not None
        assert result.year == 2024
        assert result.month == 3
        assert result.day == 15

    def test_parse_date_vietnamese_format(self):
        """Test parsing Vietnamese date format."""
        text = "Ngày 25 tháng 12 năm 2023"
        result = self.parser.parse_date(text)
        
        assert result is not None
        assert result.year == 2023
        assert result.month == 12
        assert result.day == 25

    def test_parse_date_no_date_found(self):
        """Test parsing when no date is present."""
        text = "No date information here"
        result = self.parser.parse_date(text)
        
        assert result is None

    def test_parse_amount_vietnamese_currency(self):
        """Test parsing Vietnamese currency format."""
        text = "Amount: 1.500.000 VND"
        result = self.parser.parse_amount(text)
        
        assert result is not None
        assert result == Decimal('1500000')

    def test_parse_amount_usd_format(self):
        """Test parsing USD currency format."""
        text = "Total: $1,234.56"
        result = self.parser.parse_amount(text)
        
        assert result is not None
        assert result == Decimal('1234.56')

    def test_parse_amount_no_amount_found(self):
        """Test parsing when no amount is present."""
        text = "No monetary value here"
        result = self.parser.parse_amount(text)
        
        assert result is None

    def test_parse_reference_transaction_id(self):
        """Test parsing transaction reference ID."""
        text = "Transaction ID: TXN123456789"
        result = self.parser.parse_reference(text)
        
        assert result == "TXN123456789"

    def test_parse_reference_atm_code(self):
        """Test parsing ATM reference code."""
        text = "ATM: ATM987654321"
        result = self.parser.parse_reference(text)
        
        assert result == "ATM987654321"

    def test_parse_reference_no_reference_found(self):
        """Test parsing when no reference is present."""
        text = "No reference information"
        result = self.parser.parse_reference(text)
        
        assert result is None

    def test_extract_description_explicit_description(self):
        """Test extracting explicit description field."""
        text = "Description: Transfer to John Doe\nAmount: 500000 VND"
        result = self.parser.extract_description(text)
        
        assert result == "Transfer to John Doe"

    def test_extract_description_fallback_to_meaningful_line(self):
        """Test fallback to meaningful text line."""
        text = """
        15/03/2024
        1.500.000 VND
        Payment for services rendered
        REF123456
        """
        result = self.parser.extract_description(text)
        
        assert result == "Payment for services rendered"

    def test_parse_transaction_from_text_complete_transaction(self):
        """Test parsing complete transaction with all fields."""
        text = """
        Date: 15/03/2024
        Amount: 1.500.000 VND
        Description: Transfer to supplier
        Reference: TXN123456789
        """
        
        transactions = self.parser.parse_transaction_from_text(
            text=text,
            source_file="test_image.png",
            confidence=0.95
        )
        
        assert len(transactions) == 1
        transaction = transactions[0]
        
        assert transaction.date == datetime(2024, 3, 15)
        assert transaction.amount == Decimal('1500000')
        assert transaction.description == "Transfer to supplier"
        assert transaction.reference == "TXN123456789"
        assert transaction.source_file == "test_image.png"
        assert transaction.confidence == 0.95

    def test_parse_transaction_from_text_minimal_transaction(self):
        """Test parsing transaction with minimal information."""
        text = "Amount: 250.000 VND"
        
        transactions = self.parser.parse_transaction_from_text(
            text=text,
            source_file="test_image.png",
            confidence=0.8
        )
        
        assert len(transactions) == 1
        transaction = transactions[0]
        
        assert transaction.amount == Decimal('250000')
        assert transaction.source_file == "test_image.png"
        assert transaction.confidence == 0.8

    def test_parse_transaction_from_text_insufficient_data(self):
        """Test parsing when insufficient transaction data is present."""
        text = "Some random text without transaction info"
        
        transactions = self.parser.parse_transaction_from_text(
            text=text,
            source_file="test_image.png",
            confidence=0.6
        )
        
        assert len(transactions) == 0

    def test_parse_transaction_from_text_empty_text(self):
        """Test parsing with empty or very short text."""
        text = "short"
        
        transactions = self.parser.parse_transaction_from_text(
            text=text,
            source_file="test_image.png",
            confidence=0.5
        )
        
        assert len(transactions) == 0

    @pytest.mark.parametrize("date_format,expected", [
        ("01/01/2024", datetime(2024, 1, 1)),
        ("31-12-2023", datetime(2023, 12, 31)),
        ("2024-06-15", datetime(2024, 6, 15)),
        ("25.11.2022", datetime(2022, 11, 25)),
    ])
    def test_parse_date_various_formats(self, date_format, expected):
        """Test parsing various date formats."""
        text = f"Transaction date: {date_format}"
        result = self.parser.parse_date(text)
        
        assert result == expected

    @pytest.mark.parametrize("amount_text,expected", [
        ("1.000.000 VND", Decimal('1000000')),
        ("$500.50", Decimal('500.50')),
        ("2,500,000 VND", Decimal('2500000')),
        ("€1.234,56", None),  # Unsupported format
    ])
    def test_parse_amount_various_formats(self, amount_text, expected):
        """Test parsing various amount formats."""
        text = f"Total: {amount_text}"
        result = self.parser.parse_amount(text)
        
        if expected is None:
            assert result is None
        else:
            assert result == expected 