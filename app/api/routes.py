from fastapi import APIRouter, HTTPException, Query, UploadFile

from app.models.schemas import ReceiptResponse, ScanResponse, StatsResponse
from app.services.receipt_service import get_receipt, list_receipts, process_upload
from app.services.stats_service import get_stats

router = APIRouter()


@router.post("/scan", response_model=ScanResponse)
async def scan_receipts(files: list[UploadFile]):
    return await process_upload(files)


@router.get("/receipts", response_model=list[ReceiptResponse])
async def get_receipts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    category: str | None = None,
    vendor: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
):
    return await list_receipts(
        skip=skip, limit=limit, category=category, vendor=vendor,
        date_from=date_from, date_to=date_to,
    )


@router.get("/receipts/{receipt_id}", response_model=ReceiptResponse)
async def get_receipt_detail(receipt_id: int):
    receipt = await get_receipt(receipt_id)
    if receipt is None:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return receipt


@router.get("/stats", response_model=StatsResponse)
async def get_statistics(
    date_from: str | None = None,
    date_to: str | None = None,
):
    return await get_stats(date_from=date_from, date_to=date_to)


@router.get("/health")
async def health():
    return {"status": "healthy", "version": "0.1.0"}
