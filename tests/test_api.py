import io
import json
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.core.scanner import ScanError
from app.models.database import save_receipt


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.asyncio
async def test_scan_single_file(client, mock_scanner):
    resp = await client.post(
        "/scan",
        files={"files": ("receipt.jpg", b"fake-image", "image/jpeg")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["successful"] == 1
    assert data["results"][0]["receipt"]["vendor"] == "Test Store"


@pytest.mark.asyncio
async def test_scan_invalid_file_type(client):
    resp = await client.post(
        "/scan",
        files={"files": ("doc.txt", b"hello", "text/plain")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["failed"] == 1
    assert "Unsupported" in data["results"][0]["error"]


@pytest.mark.asyncio
async def test_scan_batch_partial_success(client, mock_scanner):
    mock_scanner.side_effect = [
        mock_scanner.return_value,
        ScanError("bad image"),
    ]
    files = [
        ("files", ("good.jpg", b"img1", "image/jpeg")),
        ("files", ("bad.jpg", b"img2", "image/jpeg")),
    ]
    resp = await client.post("/scan", files=files)
    data = resp.json()
    assert data["total"] == 2
    assert data["successful"] == 1
    assert data["failed"] == 1


@pytest.mark.asyncio
async def test_scan_no_files(client):
    resp = await client.post("/scan")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_receipts_empty(client):
    resp = await client.get("/receipts")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_get_receipt_not_found(client):
    resp = await client.get("/receipts/999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_receipt_by_id(client, db):
    receipt_id = await save_receipt({
        "vendor": "TestShop",
        "total": 10.0,
        "currency": "USD",
        "date": "2026-01-01",
        "category": "groceries",
        "line_items": json.dumps([]),
        "confidence_score": 0.9,
        "filename": "test.jpg",
        "raw_response": "{}",
        "scanned_at": datetime.now().isoformat(),
    })

    resp = await client.get(f"/receipts/{receipt_id}")
    assert resp.status_code == 200
    assert resp.json()["vendor"] == "TestShop"


@pytest.mark.asyncio
async def test_stats_endpoint(client, db):
    await save_receipt({
        "vendor": "Shop",
        "total": 25.0,
        "currency": "EUR",
        "date": "2026-03-10",
        "category": "groceries",
        "line_items": json.dumps([]),
        "confidence_score": 0.9,
        "filename": "test.jpg",
        "raw_response": "{}",
        "scanned_at": datetime.now().isoformat(),
    })

    resp = await client.get("/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_spent"] == 25.0
    assert data["by_category"]["groceries"] == 25.0
