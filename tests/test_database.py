import json
from datetime import date, datetime

import pytest
import pytest_asyncio

from app.models.database import get_db_path, init_db, save_receipt, get_receipts, get_receipt_by_id


@pytest_asyncio.fixture
async def db():
    original = get_db_path()
    import app.models.database as db_module
    db_module._db_path = ":memory:"
    await init_db()
    yield
    db_module._db_path = original


SAMPLE_RECEIPT = {
    "vendor": "Lidl",
    "total": 23.45,
    "currency": "EUR",
    "date": "2026-01-15",
    "category": "groceries",
    "line_items": json.dumps([{"description": "Milk", "quantity": 2, "unit_price": 1.20, "total": 2.40}]),
    "confidence_score": 0.95,
    "filename": "receipt.jpg",
    "raw_response": '{"raw": "data"}',
    "scanned_at": datetime(2026, 1, 15, 10, 30, 0).isoformat(),
}


@pytest.mark.asyncio
async def test_save_and_get_receipt(db):
    receipt_id = await save_receipt(SAMPLE_RECEIPT)
    assert receipt_id == 1

    receipt = await get_receipt_by_id(receipt_id)
    assert receipt is not None
    assert receipt["vendor"] == "Lidl"
    assert receipt["total"] == 23.45


@pytest.mark.asyncio
async def test_get_receipt_not_found(db):
    result = await get_receipt_by_id(999)
    assert result is None


@pytest.mark.asyncio
async def test_get_receipts_empty(db):
    results = await get_receipts()
    assert results == []


@pytest.mark.asyncio
async def test_get_receipts_with_filters(db):
    await save_receipt(SAMPLE_RECEIPT)

    receipt2 = {**SAMPLE_RECEIPT, "vendor": "Aldi", "category": "restaurant", "date": "2026-03-20"}
    await save_receipt(receipt2)

    results = await get_receipts(category="groceries")
    assert len(results) == 1
    assert results[0]["vendor"] == "Lidl"

    results = await get_receipts(vendor="Aldi")
    assert len(results) == 1

    results = await get_receipts(date_from="2026-02-01")
    assert len(results) == 1
    assert results[0]["vendor"] == "Aldi"


@pytest.mark.asyncio
async def test_get_receipts_pagination(db):
    for i in range(5):
        r = {**SAMPLE_RECEIPT, "vendor": f"Shop{i}"}
        await save_receipt(r)

    results = await get_receipts(skip=0, limit=2)
    assert len(results) == 2

    results = await get_receipts(skip=3, limit=10)
    assert len(results) == 2
