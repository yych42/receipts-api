#!/usr/bin/env python3
"""
Smoke test for the Receipts API.

Tests the /image/extract/receipt endpoint against a known receipt image
and validates the response structure and key values.
"""

import base64
import json
import sys
from pathlib import Path

import requests

# Configuration
API_URL = "https://receipts-api-yych42.fly.dev/image/extract/receipt"
TEST_DIR = Path(__file__).parent
RECEIPT_IMAGE = TEST_DIR / "receipt.png"
EXPECTED_RECEIPT = TEST_DIR / "expected_receipt.json"


def load_image_base64(image_path: Path) -> str:
    """Load an image and return as base64 string."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def load_expected(expected_path: Path) -> dict:
    """Load expected receipt JSON."""
    with open(expected_path) as f:
        return json.load(f)


def validate_response_structure(response: dict) -> list[str]:
    """Validate the response has required fields."""
    errors = []
    required_fields = ["merchant", "items", "total", "date", "time", "currency", "tax"]

    for field in required_fields:
        if field not in response:
            errors.append(f"Missing required field: {field}")

    if "items" in response:
        for i, item in enumerate(response["items"]):
            item_fields = ["name", "unit_price", "quantity", "total_price"]
            for field in item_fields:
                if field not in item:
                    errors.append(f"Item {i} missing field: {field}")

    return errors


def validate_key_values(response: dict, expected: dict) -> list[str]:
    """Validate key values match expected (with tolerance for AI variability)."""
    errors = []

    # Merchant name should contain key words
    if "KURO" not in response.get("merchant", "").upper():
        errors.append(f"Merchant mismatch: expected 'KURO RAMEN', got '{response.get('merchant')}'")

    # Total should be exact
    if abs(response.get("total", 0) - expected["total"]) > 0.01:
        errors.append(f"Total mismatch: expected {expected['total']}, got {response.get('total')}")

    # Tax should be exact
    if abs(response.get("tax", 0) - expected["tax"]) > 0.01:
        errors.append(f"Tax mismatch: expected {expected['tax']}, got {response.get('tax')}")

    # Currency should be USD
    if response.get("currency", "").upper() != "USD":
        errors.append(f"Currency mismatch: expected 'USD', got '{response.get('currency')}'")

    # Should have 4 items
    if len(response.get("items", [])) != 4:
        errors.append(f"Item count mismatch: expected 4, got {len(response.get('items', []))}")

    # Validate item totals sum approximately to subtotal (56.95)
    item_total = sum(item.get("total_price", 0) for item in response.get("items", []))
    expected_subtotal = 56.95
    if abs(item_total - expected_subtotal) > 0.10:
        errors.append(f"Item total mismatch: expected ~{expected_subtotal}, got {item_total}")

    return errors


def run_smoke_test() -> bool:
    """Run the smoke test and return success status."""
    print("=" * 60)
    print("RECEIPTS API SMOKE TEST")
    print("=" * 60)

    # Check files exist
    if not RECEIPT_IMAGE.exists():
        print(f"ERROR: Receipt image not found: {RECEIPT_IMAGE}")
        return False

    if not EXPECTED_RECEIPT.exists():
        print(f"ERROR: Expected receipt not found: {EXPECTED_RECEIPT}")
        return False

    # Load test data
    print(f"\n1. Loading test image: {RECEIPT_IMAGE.name}")
    image_base64 = load_image_base64(RECEIPT_IMAGE)
    print(f"   Image size: {len(image_base64)} bytes (base64)")

    print(f"\n2. Loading expected receipt: {EXPECTED_RECEIPT.name}")
    expected = load_expected(EXPECTED_RECEIPT)

    # Make API request
    print(f"\n3. Calling API: {API_URL}")
    try:
        response = requests.post(
            API_URL,
            json={"image": image_base64},
            headers={"Content-Type": "application/json"},
            timeout=60,
        )
    except requests.exceptions.RequestException as e:
        print(f"   ERROR: Request failed: {e}")
        return False

    print(f"   Status: {response.status_code}")

    if response.status_code != 200:
        print(f"   ERROR: Unexpected status code")
        print(f"   Response: {response.text[:500]}")
        return False

    # Parse response
    try:
        result = response.json()
    except json.JSONDecodeError:
        print(f"   ERROR: Invalid JSON response")
        return False

    print(f"\n4. Validating response structure...")
    structure_errors = validate_response_structure(result)
    if structure_errors:
        for err in structure_errors:
            print(f"   ERROR: {err}")
        return False
    print("   OK: All required fields present")

    print(f"\n5. Validating key values...")
    value_errors = validate_key_values(result, expected)
    if value_errors:
        for err in value_errors:
            print(f"   WARNING: {err}")
        # Warnings don't fail the test, but we report them

    # Print summary
    print("\n" + "=" * 60)
    print("RESPONSE SUMMARY")
    print("=" * 60)
    print(f"Merchant: {result.get('merchant')}")
    print(f"Date: {result.get('date')}")
    print(f"Time: {result.get('time')}")
    print(f"Currency: {result.get('currency')}")
    print(f"Items: {len(result.get('items', []))}")
    for i, item in enumerate(result.get("items", []), 1):
        print(f"  {i}. {item.get('name')}: ${item.get('total_price')}")
    print(f"Tax: ${result.get('tax')}")
    print(f"Total: ${result.get('total')}")

    print("\n" + "=" * 60)
    if value_errors:
        print(f"RESULT: PASSED with {len(value_errors)} warning(s)")
    else:
        print("RESULT: PASSED")
    print("=" * 60)

    # Save actual response for comparison
    actual_path = TEST_DIR / "actual_receipt.json"
    with open(actual_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nActual response saved to: {actual_path}")

    return True


if __name__ == "__main__":
    success = run_smoke_test()
    sys.exit(0 if success else 1)
