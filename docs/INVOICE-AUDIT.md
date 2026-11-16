# Invoice status audit trail

InvoicePilot persists each successful **status transition** in the `invoice_events` table within the same SQLite transaction as the status update. Rejected transitions and no-op updates do not create entries.

`GET /api/invoices/{invoice_id}/events` returns the chronological event history. The events are append-only through the public API; removing direct database access, granting role-based permissions, and secure external audit storage would be necessary for production-level tamper resistance.

A test verifies draft → sent → paid, rejection of paid → draft, and missing invoices.
