"""FastAPI HTTP layer for the Reports app."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse, Response

from app.models import ReportListResponse, ReportPublic, ReportStatus
from app.reports import query, to_csv

app = FastAPI(title="SDD Workshop — Reports API", version="0.1.0")

EXPORT_ROW_CAP = 100_000


def parse_user_timezone(header: str | None) -> ZoneInfo | None:
    if not header:
        return None
    try:
        return ZoneInfo(header)
    except ZoneInfoNotFoundError:
        return None


def _filtered_page(
    *,
    status: ReportStatus | None,
    date_from: datetime | None,
    date_to: datetime | None,
    sort: str,
    descending: bool,
    offset: int,
    limit: int,
) -> tuple[list[ReportPublic], int]:
    try:
        rows = query(
            status=status,
            date_from=date_from,
            date_to=date_to,
            sort=sort,
            descending=descending,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    page = rows[offset : offset + limit]
    return [ReportPublic.from_internal(r) for r in page], len(rows)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def reports_page() -> FileResponse:
    return FileResponse(Path(__file__).parent / "static" / "reports.html")


@app.get("/reports", response_model=ReportListResponse)
def list_reports(
    status: ReportStatus | None = Query(None, description="Filter by status"),
    date_from: datetime | None = Query(None, description="Lower bound on created_at (inclusive)"),
    date_to: datetime | None = Query(None, description="Upper bound on created_at (inclusive)"),
    sort: str = Query("created_at", description="Sort field"),
    descending: bool = Query(True, description="Sort descending"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
) -> ReportListResponse:
    """Return a paginated list of reports.

    Public fields only — `internal_id` and `owner_email` are stripped via
    `ReportPublic.from_internal`.
    """

    items, total = _filtered_page(
        status=status,
        date_from=date_from,
        date_to=date_to,
        sort=sort,
        descending=descending,
        offset=offset,
        limit=limit,
    )
    return ReportListResponse(items=items, total=total, offset=offset, limit=limit)


@app.get("/reports.csv")
def export_reports_csv(
    status: ReportStatus | None = Query(None, description="Filter by status"),
    date_from: datetime | None = Query(None, description="Lower bound on created_at (inclusive)"),
    date_to: datetime | None = Query(None, description="Upper bound on created_at (inclusive)"),
    sort: str = Query("created_at", description="Sort field"),
    descending: bool = Query(True, description="Sort descending"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    x_user_timezone: str | None = Header(None, alias="X-User-Timezone"),
) -> Response:
    """Download the current reports page as CSV."""

    try:
        rows = query(
            status=status,
            date_from=date_from,
            date_to=date_to,
            sort=sort,
            descending=descending,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if len(rows) > EXPORT_ROW_CAP:
        raise HTTPException(
            status_code=413,
            detail={
                "message": f"Export exceeds maximum of {EXPORT_ROW_CAP} matching rows",
                "total": len(rows),
            },
        )

    page = rows[offset : offset + limit]
    items = [ReportPublic.from_internal(r) for r in page]
    tz = parse_user_timezone(x_user_timezone)

    return Response(
        content=to_csv(items, timezone=tz),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="reports.csv"'},
    )
