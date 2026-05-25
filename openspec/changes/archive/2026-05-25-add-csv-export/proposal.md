## Why

Product asked for a way to download the reports table as a spreadsheet. Users need to
share or analyze the rows they are already looking at without copying from the UI or
calling the JSON API by hand.

## What Changes

- Add `GET /reports.csv` that returns the **current page** of reports (same filters,
  sort, `offset`, and `limit` as `GET /reports`) as RFC 4180 CSV with a file download.
- Add a minimal **reports page** at `/` with filtering, pagination, and an **Export CSV**
  button that downloads what is on screen.
- Enforce the existing internal-field rule on CSV output (`internal_id`, `owner_email`
  MUST NOT appear).
- Format `created_at` in the user's timezone when `X-User-Timezone` is sent (UTC
  otherwise).
- Reject exports when the matching result set exceeds 100,000 rows (HTTP 413).
- Add pytest coverage in `tests/test_csv_export.py`.

## Capabilities

### New Capabilities

<!-- None — export extends the existing reports capability -->

### Modified Capabilities

- `reports`: CSV export endpoint, reports UI page, internal-field and timezone rules
  for export, row-cap guard.

## Impact

- `app/main.py` — new routes for `/`, `/reports.csv`
- `app/reports.py` — shared query + `to_csv()` serializer
- `app/static/` — reports HTML page (new)
- `tests/test_csv_export.py` — new tests (baseline `tests/test_reports.py` unchanged)
- `openspec/specs/reports/spec.md` — updated when this change is archived
