# InvoicePilot

**Finance / Billing** · Python · FastAPI · SQLite · Portfolio case study

> A FastAPI invoicing service with customers, invoice line items, tax calculations and payment status.

### At a glance

| | |
| --- | --- |
| **Core workflow** | Customers → invoice items → tax calculation → payment status |
| **Highlights** | Integer-cent amount storage, tax rounding, immutable final statuses |
| **Persistence** | Local SQLite database |
| **Maturity** | Functional portfolio MVP — not production hardened |


## Engineering edition: measurable behaviour

- **Live read-only reporting:** `GET /api/insights` derives aggregates from stored business data (not hard-coded numbers).
- **Review path:** [Five-minute walkthrough](docs/DEMO.md) · [API reference](docs/API.md) · [Engineering decisions](docs/ENGINEERING.md).
- **License:** MIT. **Operational maturity:** local educational MVP, not an internet-facing production service.
- **Container:** `docker compose up --build` binds the demo to `127.0.0.1` and stores its SQLite file in a persistent named volume.

## Product capabilities

- Customer directory
- Invoices with multiple line items and calculated totals
- Draft → sent → paid / void state updates
- Interactive API documentation at /docs

## Architecture

```mermaid
flowchart LR
  UI[Responsive web UI] --> API[Domain-specific routes]
  API --> VAL[Validation & workflows]
  VAL --> DB[Relational database]
```

### Design decisions

- **Domain-specific modelling:** the entities and routes reflect a real finance / billing workflow rather than generic records.
- **Portable setup:** the application can be run locally with documented tooling; no paid external API keys are required.
- **Explicit boundaries:** this is a demonstrable MVP. Auth, tenancy, logging, scalability and operational security need additional engineering before production use.

## Local development

```bash
python -m venv .venv
# Activate: Windows .venv\Scripts\activate; macOS/Linux source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```
Visit http://localhost:8000/docs for API documentation. There is also a demo at http://localhost:8000/.

## Tests

```bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

The GitHub Actions workflow runs integration tests of real API behaviour. These tests cover representative workflows and validations; they do not imply comprehensive security or load testing.

## API and UX

The project provides a browser-based demo and REST API documentation at `/docs`. See the application source for concrete endpoints. No hosted demo is claimed.

## Roadmap

- PDF exports; payment provider integration.
- Authentication, authorisation, secure secrets management, and deployment configuration.
- Database migrations and backups where not already available, along with comprehensive accessibility and end-to-end testing.

## Security and scope

Local demonstration only; do not deploy publicly with real customer data as-is. The `.env.example` documents configuration; do not commit `.env`, credential files, database files, or third-party API keys. See [SECURITY.md](SECURITY.md).

## Project maintenance

- [CONTRIBUTING.md](CONTRIBUTING.md) — development conventions and review expectations
- [.github/workflows/checks.yml](.github/workflows/checks.yml) — automated checks
- [CHANGELOG.md](CHANGELOG.md) — release notes
