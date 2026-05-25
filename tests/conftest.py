import json
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.models.database import init_db
import app.models.database as db_module


@pytest_asyncio.fixture
async def db():
    original_path = db_module._db_path
    db_module._db_path = ":memory:"
    await init_db()
    yield
    if db_module._shared_connection is not None:
        conn = db_module._shared_connection
        await conn.close()
        if hasattr(conn, "_thread") and conn._thread.is_alive():
            conn._thread.join(timeout=5)
        db_module._shared_connection = None
    db_module._db_path = original_path


@pytest.fixture
def mock_scanner():
    from app.models.schemas import Category, ReceiptData, LineItem

    mock_data = ReceiptData(
        vendor="Test Store",
        total=42.50,
        currency="USD",
        date="2026-01-15",
        category=Category.GROCERIES,
        line_items=[LineItem(description="Item A", quantity=1, unit_price=42.50, total=42.50)],
        confidence_score=0.95,
    )
    with patch("app.services.receipt_service.scan_receipt", new_callable=AsyncMock, return_value=mock_data) as mock:
        yield mock


@pytest_asyncio.fixture
async def client(db):
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
