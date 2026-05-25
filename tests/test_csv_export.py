"""Tests for CSV export (openspec change add-csv-export)."""

from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from app.data import all_reports
from app.main import app
from app.models import Report

client = TestClient(app)

_EDGE_TITLE = 'CSV with commas, "quotes" and newlines\nin the title'


def _csv_rows(body: str) -> list[list[str]]:
    return list(csv.reader(io.StringIO(body)))


def test_csv_matches_json_page() -> None:
    params = {"status": "approved", "limit": 5, "offset": 10, "sort": "amount"}
    json_body = client.get("/reports", params=params).json()
    csv_r = client.get("/reports.csv", params=params)
    assert csv_r.status_code == 200
    assert "text/csv" in csv_r.headers["content-type"]
    assert "attachment" in csv_r.headers["content-disposition"]
    assert csv_r.headers["content-disposition"].endswith('filename="reports.csv"')

    rows = _csv_rows(csv_r.text)
    assert rows[0] == ["id", "title", "status", "owner", "amount", "created_at"]
    assert len(rows) - 1 == len(json_body["items"])
    for csv_row, item in zip(rows[1:], json_body["items"], strict=True):
        assert int(csv_row[0]) == item["id"]
        assert csv_row[1] == item["title"]
        assert csv_row[2] == item["status"]
        assert csv_row[3] == item["owner"]
        assert float(csv_row[4]) == item["amount"]


def test_csv_omits_internal_fields() -> None:
    r = client.get("/reports.csv", params={"limit": 200})
    assert r.status_code == 200
    assert "internal_id" not in r.text
    assert "owner_email" not in r.text


def test_csv_escapes_rfc4180_edge_case_title() -> None:
    edge = next(r for r in all_reports() if r.title == _EDGE_TITLE)
    r = client.get("/reports.csv", params={"limit": 200})
    assert r.status_code == 200
    rows = _csv_rows(r.text)
    match = next(row for row in rows[1:] if int(row[0]) == edge.id)
    assert match[1] == _EDGE_TITLE
    line_for_row = next(line for line in r.text.splitlines() if line.startswith(f"{edge.id},"))
    assert line_for_row.startswith(f'{edge.id},"')
    assert '""quotes""' in line_for_row


def test_csv_honors_x_user_timezone() -> None:
    sample = client.get("/reports", params={"limit": 1}).json()["items"][0]
    utc_r = client.get("/reports.csv", params={"limit": 1, "offset": 0})
    tz_r = client.get(
        "/reports.csv",
        params={"limit": 1, "offset": 0},
        headers={"X-User-Timezone": "America/New_York"},
    )
    assert utc_r.status_code == 200
    assert tz_r.status_code == 200
    utc_cell = _csv_rows(utc_r.text)[1][5]
    tz_cell = _csv_rows(tz_r.text)[1][5]
    assert utc_cell != tz_cell
    assert "-05:00" in tz_cell or "-04:00" in tz_cell
    dt_utc = datetime.fromisoformat(sample["created_at"])
    expected = dt_utc.astimezone(ZoneInfo("America/New_York")).isoformat()
    assert tz_cell == expected


def test_csv_invalid_timezone_falls_back_to_utc() -> None:
    r = client.get(
        "/reports.csv",
        params={"limit": 1},
        headers={"X-User-Timezone": "Not/A_Real_Zone"},
    )
    plain = client.get("/reports.csv", params={"limit": 1})
    assert r.status_code == 200
    assert _csv_rows(r.text)[1][5] == _csv_rows(plain.text)[1][5]


def test_csv_rejects_bad_sort_field() -> None:
    r = client.get("/reports.csv", params={"sort": "owner_email"})
    assert r.status_code == 400


def test_csv_rejects_over_row_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = Report(
        id=1,
        internal_id="INT-000001",
        title="stub",
        status="pending",
        owner="Owner",
        owner_email="o@example.com",
        amount=1.0,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    huge = [stub] * (100_001)

    def fake_query(**kwargs: object) -> list[Report]:
        return huge

    monkeypatch.setattr("app.main.query", fake_query)
    r = client.get("/reports.csv")
    assert r.status_code == 413
    body = r.json()
    assert body["detail"]["total"] == 100_001


def test_reports_page_served() -> None:
    r = client.get("/")
    assert r.status_code == 200
    assert "Export current page" in r.text
    assert "/reports.csv" in r.text
