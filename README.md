# CommitGuard Conventional Git & Hook Validator

Conventional commit format and git message linter ensuring clean semantic release versioning.

## Target Complexity & Language
- **Language:** python
- **Complexity:** medium

## Problem Statement
Engineering repositories suffer from inconsistent commit messages which break automated changelog generators.

## Key Features
- Standard conventional commit type verification
- Optional scope syntax parser (e.g., feat(auth): ...)
- Subject line capitalization and length validation (<= 72 chars)
- Breaking change marker detection (! or BREAKING CHANGE)

## Technology Stack
- Python 3.12
- Regex
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
