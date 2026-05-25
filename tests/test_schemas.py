import json
from datetime import date

import pytest

from app.models.schemas import (
    Category,
    LineItem,
    ReceiptData,
    ReceiptResponse,
    ScanResult,
    ScanResponse,
    StatsResponse,
)


def test_line_item_defaults():
    item = LineItem(description="Coffee", unit_price=3.50, total=3.50)
    assert item.quantity == 1.0


def test_line_item_all_fields():
    item = LineItem(description="Beer", quantity=2, unit_price=5.0, total=10.0)
    assert item.quantity == 2.0
    assert item.total == 10.0


def test_category_values():
    assert Category.GROCERIES == "groceries"
    assert Category.OTHER == "other"
    assert len(Category) == 9


def test_receipt_data_full():
    data = ReceiptData(
        vendor="Lidl",
        total=23.45,
        currency="EUR",
        date=date(2026, 1, 15),
        category=Category.GROCERIES,
        line_items=[
            LineItem(description="Milk", quantity=2, unit_price=1.20, total=2.40),
            LineItem(description="Bread", unit_price=2.10, total=2.10),
        ],
        confidence_score=0.95,
    )
    assert data.vendor == "Lidl"
    assert len(data.line_items) == 2


def test_receipt_data_null_date():
    data = ReceiptData(
        vendor="Shop",
        total=10.0,
        currency="USD",
        date=None,
        category=Category.OTHER,
        line_items=[],
        confidence_score=0.5,
    )
    assert data.date is None


def test_receipt_data_from_json():
    raw = json.dumps({
        "vendor": "АТБ",
        "total": 156.80,
        "currency": "UAH",
        "date": "2026-03-10",
        "category": "groceries",
        "line_items": [
            {"description": "Молоко", "quantity": 1, "unit_price": 45.90, "total": 45.90}
        ],
        "confidence_score": 0.88,
    })
    data = ReceiptData.model_validate_json(raw)
    assert data.vendor == "АТБ"
    assert data.currency == "UAH"
    assert data.line_items[0].description == "Молоко"


def test_scan_response_counts():
    resp = ScanResponse(
        results=[
            ScanResult(filename="a.jpg", success=True, receipt=None, error=None),
            ScanResult(filename="b.jpg", success=False, receipt=None, error="bad image"),
        ],
        total=2,
        successful=1,
        failed=1,
    )
    assert resp.total == 2
    assert resp.failed == 1
