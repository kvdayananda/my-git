# TaskPulse Scheduled Workflow & Dispatcher

Reliable job scheduler and webhook event dispatcher with exponential backoff and audit logs.

## Target Complexity & Language
- **Language:** python
- **Complexity:** medium

## Problem Statement
Automated operations need a predictable execution engine that handles transient task failures with retries.

## Key Features
- Priority-based job queue (critical, normal, low)
- Retry mechanism with exponential backoff calculation
- Execution status tracking (pending, running, succeeded, failed)
- Audit trail recording timestamps and error summaries

## Technology Stack
- Python 3.12
- Dataclasses
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
