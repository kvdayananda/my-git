# CodeLens Project Architecture & Metric Inspector

Static code metrics analyzer that scans directories, computes line metrics, and identifies complexity hotspots.

## Target Complexity & Language
- **Language:** python
- **Complexity:** medium

## Problem Statement
Engineering teams need fast, local repository analysis to audit comment ratios, blank lines, and file distribution.

## Key Features
- Multi-extension code file detection (.py, .js, .ts, .go, .rs)
- Granular metric computation (total lines, blank lines, comments, code lines)
- Complexity hotspot detection based on file length thresholds
- Markdown summary report generator

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
