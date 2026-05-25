"""Reports query layer.

Pure functions that filter, sort, and paginate the in-memory dataset. Kept separate
from the HTTP layer (`main.py`) so it can be reused by any future export feature.
"""

from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Iterable
from zoneinfo import ZoneInfo

from app.data import all_reports
from app.models import Report, ReportPublic, ReportStatus


_SORTABLE_FIELDS = {"id", "title", "status", "owner", "amount", "created_at"}
_CSV_HEADERS = ("id", "title", "status", "owner", "amount", "created_at")


def query(
    *,
    status: ReportStatus | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    sort: str = "created_at",
    descending: bool = True,
) -> list[Report]:
    """Filter and sort reports. Pagination is applied by the caller."""

    if sort not in _SORTABLE_FIELDS:
        raise ValueError(f"Unsupported sort field: {sort!r}")

    rows: Iterable[Report] = all_reports()

    if status is not None:
        rows = (r for r in rows if r.status == status)
    if date_from is not None:
        rows = (r for r in rows if r.created_at >= date_from)
    if date_to is not None:
        rows = (r for r in rows if r.created_at <= date_to)

    return sorted(rows, key=lambda r: getattr(r, sort), reverse=descending)


def _format_created_at(created_at: datetime, timezone: ZoneInfo | None) -> str:
    tz = timezone or ZoneInfo("UTC")
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=ZoneInfo("UTC"))
    return created_at.astimezone(tz).isoformat()


def to_csv(items: list[ReportPublic], *, timezone: ZoneInfo | None) -> str:
    """Serialize report rows to RFC 4180 CSV."""

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(_CSV_HEADERS)
    for item in items:
        writer.writerow(
            [
                item.id,
                item.title,
                item.status,
                item.owner,
                item.amount,
                _format_created_at(item.created_at, timezone),
            ]
        )
    return buffer.getvalue()
