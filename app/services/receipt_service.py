import json
import logging
from datetime import datetime

from fastapi import UploadFile

from app.core.config import settings
from app.core.scanner import ScanError, scan_receipt
from app.models.database import get_receipt_by_id, get_receipts, save_receipt
from app.models.schemas import ReceiptResponse, ScanResponse, ScanResult

logger = logging.getLogger(__name__)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}


async def process_upload(files: list[UploadFile]) -> ScanResponse:
    results: list[ScanResult] = []

    for file in files:
        filename = file.filename or "unknown"

        if file.content_type not in ALLOWED_TYPES:
            results.append(ScanResult(
                filename=filename,
                success=False,
                error=f"Unsupported file type: {file.content_type}. Allowed: JPEG, PNG, WebP, PDF",
            ))
            continue

        file_bytes = await file.read()

        if len(file_bytes) > settings.max_file_size_mb * 1024 * 1024:
            results.append(ScanResult(
                filename=filename,
                success=False,
                error=f"File too large. Maximum size: {settings.max_file_size_mb}MB",
            ))
            continue

        try:
            receipt_data = await scan_receipt(file_bytes, file.content_type)
        except ScanError as e:
            results.append(ScanResult(filename=filename, success=False, error=str(e)))
            continue

        now = datetime.utcnow()
        receipt_id = await save_receipt({
            "vendor": receipt_data.vendor,
            "total": receipt_data.total,
            "currency": receipt_data.currency,
            "date": receipt_data.date.isoformat() if receipt_data.date else None,
            "category": receipt_data.category.value,
            "line_items": json.dumps([item.model_dump() for item in receipt_data.line_items]),
            "confidence_score": receipt_data.confidence_score,
            "filename": filename,
            "raw_response": receipt_data.model_dump_json(),
            "scanned_at": now.isoformat(),
        })

        receipt_response = ReceiptResponse(
            id=receipt_id,
            filename=filename,
            scanned_at=now,
            **receipt_data.model_dump(),
        )
        results.append(ScanResult(filename=filename, success=True, receipt=receipt_response))

    successful = sum(1 for r in results if r.success)
    return ScanResponse(
        results=results,
        total=len(results),
        successful=successful,
        failed=len(results) - successful,
    )


def _row_to_response(row: dict) -> ReceiptResponse:
    return ReceiptResponse(
        id=row["id"],
        vendor=row["vendor"],
        total=row["total"],
        currency=row["currency"],
        date=row["date"],
        category=row["category"],
        line_items=json.loads(row["line_items"]),
        confidence_score=row["confidence_score"],
        filename=row["filename"],
        scanned_at=row["scanned_at"],
    )


async def list_receipts(
    skip: int = 0,
    limit: int = 50,
    category: str | None = None,
    vendor: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[ReceiptResponse]:
    rows = await get_receipts(skip=skip, limit=limit, category=category, vendor=vendor, date_from=date_from, date_to=date_to)
    return [_row_to_response(row) for row in rows]


async def get_receipt(receipt_id: int) -> ReceiptResponse | None:
    row = await get_receipt_by_id(receipt_id)
    if row is None:
        return None
    return _row_to_response(row)
