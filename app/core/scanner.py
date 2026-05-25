import base64
import logging

import anthropic

from app.core.config import settings
from app.models.schemas import ReceiptData

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a receipt and invoice data extraction system. Extract structured data from the provided receipt or invoice image.

Return ONLY a valid JSON object with exactly these fields:
{
  "vendor": "store or company name",
  "total": 0.00,
  "currency": "ISO 4217 code (USD, EUR, UAH, GBP, etc.)",
  "date": "YYYY-MM-DD or null if not visible",
  "category": "one of: groceries, restaurant, transport, fuel, entertainment, utilities, healthcare, shopping, other",
  "line_items": [
    {"description": "item name", "quantity": 1.0, "unit_price": 0.00, "total": 0.00}
  ],
  "confidence_score": 0.0
}

Rules:
- Return raw JSON only. No markdown, no code fences, no explanations.
- confidence_score: rate 0.0 to 1.0 based on image clarity and extraction certainty.
  1.0 = everything clearly visible and extracted. 0.7 = most data clear, some guessed.
  0.5 = partial data, significant guessing. 0.2 = very poor quality, mostly guessed.
- If the receipt is in any non-English language, still extract all data correctly.
- If a field is not visible, use best guess or null for date.
- line_items should capture each distinct product/service on the receipt.
- currency should be the ISO 4217 code, inferred from language/country if not explicit."""

MODEL = "claude-sonnet-4-20250514"


class ScanError(Exception):
    pass


def _get_client() -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)


def _build_content_block(file_bytes: bytes, media_type: str) -> dict:
    encoded = base64.standard_b64encode(file_bytes).decode("utf-8")

    if media_type == "application/pdf":
        return {
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": encoded,
            },
        }

    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": encoded,
        },
    }


async def scan_receipt(file_bytes: bytes, media_type: str) -> ReceiptData:
    client = _get_client()
    content_block = _build_content_block(file_bytes, media_type)

    last_error: Exception | None = None
    for attempt in range(2):
        response = await client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        content_block,
                        {"type": "text", "text": "Extract all data from this receipt."},
                    ],
                }
            ],
        )

        raw_text = response.content[0].text

        try:
            data = ReceiptData.model_validate_json(raw_text)
        except Exception as e:
            last_error = e
            logger.warning("JSON parse attempt %d failed: %s", attempt + 1, e)
            continue

        if data.confidence_score < 0.1:
            raise ScanError("Image unreadable — confidence too low")

        return data

    raise ScanError(f"Failed to parse Claude response after 2 attempts: {last_error}")
