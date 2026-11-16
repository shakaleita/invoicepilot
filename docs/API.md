# HTTP interface

Main operations:

- `GET/POST /api/customers`
- `GET/POST /api/invoices`
- `GET /api/invoices/{id}`
- `PATCH /api/invoices/{id}/status`

Additional read-only endpoints:

- `GET /api/insights` — aggregated product metrics
- `GET /api/health` — dependency/availability probe

These endpoints are demonstration APIs; no public authentication is implemented. See source and tests for payload fields and status codes.
