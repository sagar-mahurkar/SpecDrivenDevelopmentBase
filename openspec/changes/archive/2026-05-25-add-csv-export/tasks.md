## 1. CSV serialization layer

- [x] 1.1 Add `to_csv(items, *, timezone: ZoneInfo | None)` in `app/reports.py` using the
  stdlib `csv` module with headers `id,title,status,owner,amount,created_at`
- [x] 1.2 Format `created_at` per `timezone` (UTC when `None`) as ISO 8601 with offset

## 2. HTTP endpoints

- [x] 2.1 Extract shared `_filtered_page()` in `app/main.py` used by JSON and CSV routes
- [x] 2.2 Add `GET /reports.csv` returning `text/csv` with `Content-Disposition:
  attachment; filename="reports.csv"`, parsing `X-User-Timezone`
- [x] 2.3 Return HTTP 413 when filtered row count exceeds 100,000
- [x] 2.4 Refactor `GET /reports` to use `_filtered_page()` (behavior unchanged)

## 3. Reports UI

- [x] 3.1 Add `app/static/reports.html` with filters, pagination, and Export CSV link
- [x] 3.2 Serve the page at `GET /` via `FileResponse`

## 4. Tests

- [x] 4.1 Create `tests/test_csv_export.py` covering page parity with JSON, internal-field
  omission, RFC 4180 edge-case title, timezone header, bad sort → 400, and 413 cap
- [x] 4.2 Run `pytest -q` and ensure all baseline tests still pass
