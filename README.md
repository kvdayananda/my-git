# Nexus REST API & Telemetry Engine

High-performance modular REST API service featuring metric ingestion, health telemetry, and status reporting.

## Problem Statement
Distributed microservices require an authenticated, low-overhead endpoint to aggregate periodic operational heartbeats and metrics.

## Key Features
- Payload ingestion with Pydantic validation
- In-memory time-series metric registry with moving averages
- System health and uptime telemetry endpoints
- JSON format export and query filtering by service name

## Technology Stack
- Python 3.12
- FastAPI / Starlette
- Pydantic
- Pytest


## Installation & Setup
```bash
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## Running Unit Tests
```bash
pytest -v
```

---
*Generated, verified in Docker sandbox, and published automatically by [GitAuto AI](https://github.com).*
