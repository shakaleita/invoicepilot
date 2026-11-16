# InvoicePilot — Engineering Case Study & Quality Roadmap

**Portfolio:** [Digital Solution9](https://github.com/shakaleita/teamforge-saas/blob/main/PORTFOLIO.md) · **Repository:** [Source](https://github.com/shakaleita/invoicepilot)  
**Stack:** Python, FastAPI, SQLite · **Status:** Local portfolio MVP; not production-certified.

## Implemented domain workflow
Customer billing, invoice line items, integer-cent totals, tax rounding and status changes.

## Domain invariants
Money must use integer minor units, completed invoice totals must not drift, and paid/void status transitions must be immutable.

## Verification backlog (future work)
- Tax and rounding edge cases verified against fixtures
- Paid invoice remains immutable after new update attempts
- Concurrent payment state updates cannot duplicate a transition

## High-value engineering upgrades
1. Add scoped users, invoice numbering and idempotent issue/send APIs
2. Create exportable invoice PDFs using verified data
3. Add accounting reconciliation tests and payment integration sandbox

## Production release gate

Pass permission-boundary tests, validate concurrency and financial or domain invariants, verify database migrations, run CI and browser tests, deploy synthetic-data staging, measure performance, test accessibility, and document threat mitigations. The open issues in this file are not completed features.

**Scope:** Engineering roadmap, not a certification of readiness.
