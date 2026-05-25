## Context

The Reports API today exposes `GET /reports` (JSON, paginated) and `GET /health`.
Filtering and sorting live in `app/reports.query()`. Public fields are defined on
`ReportPublic`; internal fields must never leak.

The PM request is explicit: export **what is currently showing** on the reports page,
not the entire filtered dataset across all pages.

## Goals / Non-Goals

**Goals:**

- `GET /reports.csv` accepts the same query parameters as `GET /reports` and returns
  exactly the rows in `[offset : offset + limit]` after filter/sort.
- CSV uses the stdlib `csv` module (RFC 4180), columns matching `ReportPublic` fields.
- A simple reports page at `/` drives filters/pagination and links Export CSV to
  `/reports.csv` with the same query string.
- Honor `X-User-Timezone` for `created_at` formatting in CSV.
- Cap exports at 100,000 matching rows → HTTP 413 with a JSON `detail` body.

**Non-Goals:**

- XLSX/PDF, auth, scheduled/email export, database (per `AGENTS.md`).
- Exporting all pages in one download (user must change page or raise `limit`).

## Decisions

### 1. Endpoint: `GET /reports.csv` (not `/reports/export`)

**Rationale:** Treats CSV as an alternate representation of the reports resource;
matches the workshop delta-spec example and keeps filter params identical to JSON.

**Alternative considered:** `/reports/export` — rejected to stay aligned with OpenSpec
workshop docs.

### 2. Page scope: same `offset` + `limit` as JSON

**Rationale:** Matches "download what's currently showing." Reuses `query()` then
slices `rows[offset : offset + limit]` — same code path as `list_reports`.

**Alternative considered:** Export all filtered rows — rejected; contradicts PM ask
and could surprise users on large datasets.

### 3. Shared `_filtered_page()` helper in `main.py`

**Rationale:** JSON and CSV endpoints must not drift on filter/sort/pagination logic.

### 4. `to_csv()` in `app/reports.py`

**Rationale:** Keeps HTTP layer thin; serializer is unit-testable and reusable.

Columns (header row): `id`, `title`, `status`, `owner`, `amount`, `created_at`.

### 5. Timezone formatting

Parse `X-User-Timezone` (IANA name, e.g. `America/New_York`). On invalid/missing
header, use UTC. Format as ISO 8601 offset datetime string in CSV cells.

Use `zoneinfo` (stdlib 3.9+).

### 6. Row cap before serialization

After `query()`, if `len(rows) > 100_000`, return 413 before building CSV. With the
seed dataset (120 rows) this is only exercised in tests via a documented constant or
mock — no perf issue today.

### 7. Reports UI: static `app/static/reports.html` served at `/`

Single HTML file, vanilla JS calling `/reports` and setting Export link to
`/reports.csv?{same params}`. No frontend build step.

## Risks / Trade-offs

- **[Risk] Users expect full export** → Mitigation: UI copy shows "Export current page";
  they can raise `limit` (max 200 per API) for a larger slice.
- **[Risk] Excel locale vs RFC 4180** → Mitigation: RFC 4180 via `csv` module; seed data
  includes commas/quotes/newlines in titles to validate escaping.
- **[Risk] Timezone header abuse** → Mitigation: invalid zone falls back to UTC; no crash.

## Migration Plan

Deploy as additive routes. No breaking changes to `GET /reports` or `/health`.
Rollback: remove new routes and static file.

## Open Questions

None — requirements are sufficient to implement.
