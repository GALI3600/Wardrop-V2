"""
EAN/GTIN validation with check digit verification (mod-10 algorithm).

Accepts EAN-8, UPC-12, EAN-13, and GTIN-14. Rejects internal SKU codes
that marketplaces sometimes expose via schema.org fields.
"""


def validate_ean(code: str) -> str | None:
    """Validate an EAN/GTIN code.

    Returns the cleaned code if valid, None if invalid.
    Accepts: EAN-8 (8), UPC-12 (12), EAN-13 (13), GTIN-14 (14).
    """
    code = code.strip()
    if not code.isdigit():
        return None
    if len(code) not in (8, 12, 13, 14):
        return None

    # Check digit validation (GS1 mod-10 algorithm)
    digits = [int(d) for d in code]
    check = digits[-1]
    payload = digits[:-1]

    # Weight pattern: for even-length codes (8, 12, 14) starts with 3,1,3,1...
    # For odd-length codes (13) starts with 1,3,1,3...
    total = 0
    for i, d in enumerate(payload):
        if len(code) in (13,):
            weight = 3 if i % 2 == 1 else 1
        else:
            weight = 3 if i % 2 == 0 else 1
        total += d * weight

    expected = (10 - total % 10) % 10
    return code if expected == check else None
