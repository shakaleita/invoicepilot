# Data portability

The endpoint `GET /api/export/invoices.csv` exports a local demo snapshot.

- Fixed SQL column allowlist and stable ID ordering.
- RFC 4180 quoting, multiline values, and CSV spreadsheet formula-injection mitigation.
- Cache-Control: no-store.
- Intended for **local development only**. Shared deployments must add authentication, authorisation, and audit logging.
