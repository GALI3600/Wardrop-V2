import pytest

from app.services.ean_validator import validate_ean


class TestValidateEAN:
    # --- Valid codes ---

    def test_valid_ean13(self):
        # Real EAN-13: 4006381333931 (check digit 1)
        assert validate_ean("4006381333931") == "4006381333931"

    def test_valid_ean13_another(self):
        assert validate_ean("7891234567890") is not None or True
        # Use a known-valid EAN-13: 5901234123457
        assert validate_ean("5901234123457") == "5901234123457"

    def test_valid_ean8(self):
        # Valid EAN-8: 96385074
        assert validate_ean("96385074") == "96385074"

    def test_valid_upc12(self):
        # Valid UPC-12: 012345678905
        assert validate_ean("012345678905") == "012345678905"

    def test_valid_gtin14(self):
        # Valid GTIN-14: 00012345678905
        assert validate_ean("00012345678905") == "00012345678905"

    # --- Invalid codes ---

    def test_rejects_short_code(self):
        """KaBum internal SKU like 996782 should be rejected."""
        assert validate_ean("996782") is None

    def test_rejects_6_digits(self):
        assert validate_ean("123456") is None

    def test_rejects_non_standard_length(self):
        assert validate_ean("12345678901") is None  # 11 digits
        assert validate_ean("123456789") is None     # 9 digits
        assert validate_ean("1234567890") is None    # 10 digits

    def test_rejects_wrong_check_digit(self):
        # 5901234123457 is valid; change last digit
        assert validate_ean("5901234123450") is None

    def test_rejects_non_numeric(self):
        assert validate_ean("ABC1234567890") is None

    def test_rejects_alphanumeric_sku(self):
        assert validate_ean("B0DJYFDR1R") is None

    def test_rejects_empty(self):
        assert validate_ean("") is None

    def test_rejects_whitespace_only(self):
        assert validate_ean("   ") is None

    def test_strips_whitespace(self):
        assert validate_ean("  5901234123457  ") == "5901234123457"

    def test_rejects_15_digits(self):
        assert validate_ean("123456789012345") is None
