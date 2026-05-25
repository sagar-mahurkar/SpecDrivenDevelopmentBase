## ADDED Requirements

### Requirement: Export current reports page as CSV
THE system SHALL expose `GET /reports.csv` returning the current page of reports as
RFC 4180 CSV suitable for download.

#### Scenario: same page as JSON list
- **WHEN** the user calls `GET /reports.csv` with the same query parameters as a prior
  `GET /reports` call (`status`, `date_from`, `date_to`, `sort`, `descending`,
  `offset`, `limit`)
- **THEN** the CSV body SHALL contain exactly the same report rows as the JSON
  `items` array for that call, in the same order
- **AND** the response `Content-Type` SHALL be `text/csv`
- **AND** the response SHALL include `Content-Disposition: attachment` with a
  `.csv` filename

#### Scenario: CSV columns match public fields
- **WHEN** the user downloads CSV
- **THEN** the header row SHALL be `id,title,status,owner,amount,created_at`
- **AND** each data row SHALL contain only those public fields

#### Scenario: filter and sort parity
- **WHEN** the user passes the same filters and sort parameters as to `GET /reports`
- **THEN** the exported rows SHALL be the slice `[offset : offset + limit]` of the
  filtered, sorted result set

#### Scenario: invalid sort field
- **WHEN** the user passes a `sort` value that is not a permitted sort field
- **THEN** the response SHALL be HTTP 400 with the same error semantics as `GET /reports`

#### Scenario: row cap exceeded
- **WHEN** the filtered result set contains more than 100,000 rows
- **THEN** the response SHALL be HTTP 413 with a structured error body

#### Scenario: RFC 4180 escaping
- **WHEN** a report field contains commas, double quotes, or newlines
- **THEN** the CSV SHALL escape those fields per RFC 4180 using the standard-library
  `csv` module

### Requirement: Internal fields are never exposed in CSV
THE system SHALL never include `internal_id` or `owner_email` in CSV export output.

#### Scenario: omitted from CSV body
- **WHEN** the user downloads CSV for any query
- **THEN** the response body SHALL NOT contain the substrings `internal_id` or
  `owner_email`

### Requirement: CSV timestamps honor user timezone
THE system SHALL format `created_at` in the CSV using the IANA timezone from the
`X-User-Timezone` request header when valid, otherwise UTC.

#### Scenario: timezone header provided
- **WHEN** the user calls `GET /reports.csv` with a valid `X-User-Timezone` header
- **THEN** each `created_at` cell SHALL be an ISO 8601 datetime in that timezone

#### Scenario: missing or invalid timezone
- **WHEN** the header is absent or not a valid IANA zone
- **THEN** each `created_at` cell SHALL be formatted in UTC

### Requirement: Reports page with export control
THE system SHALL serve a reports page at `GET /` that lists reports and provides an
Export CSV control.

#### Scenario: page loads data from API
- **WHEN** the user opens `GET /`
- **THEN** the page SHALL display reports by calling `GET /reports` with user-selected
  filters and pagination

#### Scenario: export button matches current view
- **WHEN** the user activates Export CSV on the page
- **THEN** the browser SHALL download CSV from `GET /reports.csv` using the same
  query parameters as the currently displayed list
