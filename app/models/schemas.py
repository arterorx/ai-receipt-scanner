from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel


class Category(str, Enum):
    GROCERIES = "groceries"
    RESTAURANT = "restaurant"
    TRANSPORT = "transport"
    FUEL = "fuel"
    ENTERTAINMENT = "entertainment"
    UTILITIES = "utilities"
    HEALTHCARE = "healthcare"
    SHOPPING = "shopping"
    OTHER = "other"


class LineItem(BaseModel):
    description: str
    quantity: float = 1.0
    unit_price: float
    total: float


class ReceiptData(BaseModel):
    vendor: str
    total: float
    currency: str
    date: date | None
    category: Category
    line_items: list[LineItem]
    confidence_score: float


class ReceiptResponse(ReceiptData):
    id: int
    filename: str
    scanned_at: datetime


class ScanResult(BaseModel):
    filename: str
    success: bool
    receipt: ReceiptResponse | None = None
    error: str | None = None


class ScanResponse(BaseModel):
    results: list[ScanResult]
    total: int
    successful: int
    failed: int


class StatsResponse(BaseModel):
    by_category: dict[str, float]
    by_month: dict[str, float]
    total_spent: float
    period: dict[str, str] | None = None
