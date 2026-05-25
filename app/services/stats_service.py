import aiosqlite

from app.models.database import _connect
from app.models.schemas import StatsResponse


async def get_stats(
    date_from: str | None = None,
    date_to: str | None = None,
) -> StatsResponse:
    where = "WHERE 1=1"
    params: list = []

    if date_from:
        where += " AND date >= ?"
        params.append(date_from)
    if date_to:
        where += " AND date <= ?"
        params.append(date_to)

    async with _connect() as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            f"SELECT category, SUM(total) as sum_total FROM receipts {where} GROUP BY category",
            params,
        )
        by_category = {row["category"]: row["sum_total"] for row in await cursor.fetchall()}

        cursor = await db.execute(
            f"SELECT strftime('%Y-%m', date) as month, SUM(total) as sum_total "
            f"FROM receipts {where} AND date IS NOT NULL GROUP BY month ORDER BY month",
            params,
        )
        by_month = {row["month"]: row["sum_total"] for row in await cursor.fetchall()}

        cursor = await db.execute(
            f"SELECT COALESCE(SUM(total), 0) as total FROM receipts {where}",
            params,
        )
        row = await cursor.fetchone()
        total_spent = row["total"]

    period = None
    if date_from or date_to:
        period = {"date_from": date_from, "date_to": date_to}

    return StatsResponse(
        by_category=by_category,
        by_month=by_month,
        total_spent=total_spent,
        period=period,
    )
