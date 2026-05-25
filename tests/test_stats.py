import json
from datetime import datetime

import pytest
import pytest_asyncio

from app.models.database import init_db, save_receipt
from app.services.stats_service import get_stats
import app.models.database as db_module


@pytest_asyncio.fixture
async def db():
    original = db_module._db_path
    db_module._db_path = ":memory:"
    await init_db()
    yield
    db_module._db_path = original


def _receipt(vendor: str, total: float, category: str, date: str):
    return {
        "vendor": vendor,
        "total": total,
        "currency": "EUR",
        "date": date,
        "category": category,
        "line_items": json.dumps([]),
        "confidence_score": 0.9,
        "filename": f"{vendor}.jpg",
        "raw_response": "{}",
        "scanned_at": datetime.now().isoformat(),
    }


@pytest.mark.asyncio
async def test_stats_empty_db(db):
    stats = await get_stats()
    assert stats.total_spent == 0
    assert stats.by_category == {}
    assert stats.by_month == {}


@pytest.mark.asyncio
async def test_stats_by_category(db):
    await save_receipt(_receipt("Lidl", 20.0, "groceries", "2026-01-10"))
    await save_receipt(_receipt("Aldi", 30.0, "groceries", "2026-01-15"))
    await save_receipt(_receipt("Shell", 50.0, "fuel", "2026-01-20"))

    stats = await get_stats()
    assert stats.by_category["groceries"] == 50.0
    assert stats.by_category["fuel"] == 50.0
    assert stats.total_spent == 100.0


@pytest.mark.asyncio
async def test_stats_by_month(db):
    await save_receipt(_receipt("A", 10.0, "groceries", "2026-01-10"))
    await save_receipt(_receipt("B", 20.0, "groceries", "2026-02-15"))
    await save_receipt(_receipt("C", 30.0, "groceries", "2026-02-20"))

    stats = await get_stats()
    assert stats.by_month["2026-01"] == 10.0
    assert stats.by_month["2026-02"] == 50.0


@pytest.mark.asyncio
async def test_stats_date_filter(db):
    await save_receipt(_receipt("A", 10.0, "groceries", "2026-01-10"))
    await save_receipt(_receipt("B", 20.0, "groceries", "2026-03-15"))

    stats = await get_stats(date_from="2026-02-01")
    assert stats.total_spent == 20.0
    assert "2026-01" not in stats.by_month
    assert stats.period == {"date_from": "2026-02-01", "date_to": None}
