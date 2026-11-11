# Sentient NLP Classification & Sentiment Engine

Lexicon and token-frequency text classification engine with polarity scoring and intent categorization.

## Target Complexity & Language
- **Language:** python
- **Complexity:** medium

## Problem Statement
Automated pipelines need fast text classification and sentiment detection without heavy multi-gigabyte neural weight dependencies.

## Key Features
- N-gram tokenizer with stop-word suppression
- Polarity score calculator (-1.0 to +1.0 scale)
- Multi-class intent classifier (inquiry, bug_report, praise, complaint)
- Batch text evaluation with confidence intervals

## Technology Stack
- Python 3.12
- Math / Statistics
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
