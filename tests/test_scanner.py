import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.scanner import scan_receipt, ScanError


VALID_RESPONSE_JSON = json.dumps({
    "vendor": "Lidl",
    "total": 23.45,
    "currency": "EUR",
    "date": "2026-01-15",
    "category": "groceries",
    "line_items": [
        {"description": "Milk", "quantity": 2, "unit_price": 1.20, "total": 2.40},
        {"description": "Bread", "quantity": 1, "unit_price": 2.10, "total": 2.10},
    ],
    "confidence_score": 0.95,
})


def _mock_claude_response(text: str):
    content_block = MagicMock()
    content_block.text = text
    response = MagicMock()
    response.content = [content_block]
    return response


@pytest.mark.asyncio
@patch("app.core.scanner._get_client")
async def test_scan_receipt_jpeg(mock_get_client):
    client = AsyncMock()
    client.messages.create = AsyncMock(return_value=_mock_claude_response(VALID_RESPONSE_JSON))
    mock_get_client.return_value = client

    result = await scan_receipt(b"fake-jpeg-bytes", "image/jpeg")

    assert result.vendor == "Lidl"
    assert result.total == 23.45
    assert result.currency == "EUR"
    assert len(result.line_items) == 2
    assert result.confidence_score == 0.95


@pytest.mark.asyncio
@patch("app.core.scanner._get_client")
async def test_scan_receipt_pdf(mock_get_client):
    client = AsyncMock()
    client.messages.create = AsyncMock(return_value=_mock_claude_response(VALID_RESPONSE_JSON))
    mock_get_client.return_value = client

    result = await scan_receipt(b"fake-pdf-bytes", "application/pdf")

    assert result.vendor == "Lidl"
    call_args = client.messages.create.call_args
    content = call_args.kwargs["messages"][0]["content"][0]
    assert content["type"] == "document"
    assert content["source"]["media_type"] == "application/pdf"


@pytest.mark.asyncio
@patch("app.core.scanner._get_client")
async def test_scan_receipt_low_confidence(mock_get_client):
    low_conf = json.dumps({
        "vendor": "",
        "total": 0,
        "currency": "USD",
        "date": None,
        "category": "other",
        "line_items": [],
        "confidence_score": 0.05,
    })
    client = AsyncMock()
    client.messages.create = AsyncMock(return_value=_mock_claude_response(low_conf))
    mock_get_client.return_value = client

    with pytest.raises(ScanError, match="unreadable"):
        await scan_receipt(b"blurry-image", "image/jpeg")


@pytest.mark.asyncio
@patch("app.core.scanner._get_client")
async def test_scan_receipt_invalid_json_retries(mock_get_client):
    client = AsyncMock()
    client.messages.create = AsyncMock(
        side_effect=[
            _mock_claude_response("not valid json {{{"),
            _mock_claude_response(VALID_RESPONSE_JSON),
        ]
    )
    mock_get_client.return_value = client

    result = await scan_receipt(b"image-bytes", "image/png")
    assert result.vendor == "Lidl"
    assert client.messages.create.call_count == 2


@pytest.mark.asyncio
@patch("app.core.scanner._get_client")
async def test_scan_receipt_invalid_json_fails_after_retry(mock_get_client):
    client = AsyncMock()
    client.messages.create = AsyncMock(
        return_value=_mock_claude_response("still not json")
    )
    mock_get_client.return_value = client

    with pytest.raises(ScanError, match="parse"):
        await scan_receipt(b"image-bytes", "image/jpeg")

    assert client.messages.create.call_count == 2
