import aiosqlite

from app.core.config import settings

_db_path: str = settings.database_path
_shared_connection: aiosqlite.Connection | None = None


def get_db_path() -> str:
    return _db_path


def _connect():
    if _shared_connection is not None:
        return _SharedConnectionContext(_shared_connection)
    return aiosqlite.connect(_db_path)


class _SharedConnectionContext:
    """Wraps an existing connection so it can be used in async with blocks without closing it."""

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def __aenter__(self) -> aiosqlite.Connection:
        return self._conn

    async def __aexit__(self, *args) -> None:
        pass  # Don't close the shared connection


async def init_db():
    global _shared_connection
    if _db_path == ":memory:":
        # Always create a fresh in-memory connection for each init_db call.
        # This ensures test isolation when the event loop changes between tests.
        if _shared_connection is not None:
            try:
                await _shared_connection.close()
            except Exception:
                pass
        _shared_connection = await aiosqlite.connect(":memory:")
    async with _connect() as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor TEXT NOT NULL,
                total REAL NOT NULL,
                currency TEXT NOT NULL,
                date TEXT,
                category TEXT NOT NULL,
                line_items TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                filename TEXT NOT NULL,
                raw_response TEXT NOT NULL,
                scanned_at TEXT NOT NULL
            )
        """)
        await db.commit()


async def save_receipt(data: dict) -> int:
    async with _connect() as db:
        cursor = await db.execute(
            """
            INSERT INTO receipts (vendor, total, currency, date, category, line_items,
                                  confidence_score, filename, raw_response, scanned_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["vendor"],
                data["total"],
                data["currency"],
                data["date"],
                data["category"],
                data["line_items"],
                data["confidence_score"],
                data["filename"],
                data["raw_response"],
                data["scanned_at"],
            ),
        )
        await db.commit()
        return cursor.lastrowid


async def get_receipt_by_id(receipt_id: int) -> dict | None:
    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM receipts WHERE id = ?", (receipt_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_receipts(
    skip: int = 0,
    limit: int = 50,
    category: str | None = None,
    vendor: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    query = "SELECT * FROM receipts WHERE 1=1"
    params: list = []

    if category:
        query += " AND category = ?"
        params.append(category)
    if vendor:
        query += " AND vendor LIKE ?"
        params.append(f"%{vendor}%")
    if date_from:
        query += " AND date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND date <= ?"
        params.append(date_to)

    query += " ORDER BY scanned_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, skip])

    async with _connect() as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
