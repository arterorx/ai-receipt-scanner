# AI Receipt Scanner

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)
[![Claude API](https://img.shields.io/badge/Claude_API-Vision-purple.svg)](https://docs.anthropic.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

AI-powered receipt and invoice processor. Upload a photo of any receipt — get clean, structured JSON data back. Supports receipts in any language.

## Quick Start

```bash
git clone https://github.com/arterorx/ai-receipt-scanner.git && cd ai-receipt-scanner
cp .env.example .env  # add your ANTHROPIC_API_KEY
docker-compose up
```

The API is available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

## API

### Scan a receipt

```bash
curl -X POST http://localhost:8000/scan \
  -F "files=@receipt.jpg"
```

Response:

```json
{
  "results": [
    {
      "filename": "receipt.jpg",
      "success": true,
      "receipt": {
        "id": 1,
        "vendor": "Lidl",
        "total": 23.45,
        "currency": "EUR",
        "date": "2026-01-15",
        "category": "groceries",
        "line_items": [
          {"description": "Milk", "quantity": 2, "unit_price": 1.20, "total": 2.40},
          {"description": "Bread", "quantity": 1, "unit_price": 2.10, "total": 2.10}
        ],
        "confidence_score": 0.95,
        "filename": "receipt.jpg",
        "scanned_at": "2026-01-15T10:30:00"
      }
    }
  ],
  "total": 1,
  "successful": 1,
  "failed": 0
}
```

### Batch upload

```bash
curl -X POST http://localhost:8000/scan \
  -F "files=@receipt1.jpg" \
  -F "files=@receipt2.png" \
  -F "files=@invoice.pdf"
```

### List receipts

```bash
# All receipts
curl http://localhost:8000/receipts

# Filter by category
curl "http://localhost:8000/receipts?category=groceries"

# Filter by date range
curl "http://localhost:8000/receipts?date_from=2026-01-01&date_to=2026-01-31"
```

### Get receipt details

```bash
curl http://localhost:8000/receipts/1
```

### Spending statistics

```bash
curl http://localhost:8000/stats
```

```json
{
  "by_category": {"groceries": 156.80, "fuel": 45.00, "restaurant": 32.50},
  "by_month": {"2026-01": 120.30, "2026-02": 114.00},
  "total_spent": 234.30,
  "period": null
}
```

## Architecture

```
Receipt Image/PDF ──► FastAPI ──► Claude Vision API ──► Structured JSON ──► SQLite
                       │                                      │
                       ├── File validation (type, size)       ├── Pydantic validation
                       ├── Batch processing                   ├── Auto-categorization
                       └── Error handling per file             └── Confidence scoring
```

**How it works:**
1. User uploads one or more receipt images (JPEG, PNG, WebP) or PDFs
2. Each file is validated for type and size (max 10MB)
3. Images are sent to Claude Vision API with a structured extraction prompt
4. Claude returns JSON with vendor, total, currency, date, line items, and category
5. Data is validated with Pydantic, scored for confidence, and saved to SQLite
6. Aggregated statistics available via `/stats` endpoint

**Supported formats:** JPEG, PNG, WebP (as images), PDF (native document support)

**Multi-language:** Works with receipts in any language — Ukrainian, German, English, and more.

## Development

```bash
# Install dependencies
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run locally
cp .env.example .env  # add your ANTHROPIC_API_KEY
uvicorn app.main:app --reload

# Run tests
pytest tests/ -v
```

## Built With

- [Claude Vision API](https://docs.anthropic.com) — AI-powered receipt data extraction
- [FastAPI](https://fastapi.tiangolo.com) — async Python web framework
- [Pydantic v2](https://docs.pydantic.dev) — data validation and serialization
- [aiosqlite](https://github.com/omnilib/aiosqlite) — async SQLite

## License

MIT — see [LICENSE](LICENSE) for details.
