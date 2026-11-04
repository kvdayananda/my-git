"""
Core Application Module for my-git
Automated and verified by GitAuto AI.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from typing import Any, Optional


@dataclass
class Record:
    """Represents a validated data record."""
    id: str
    title: str
    priority: str = "medium"
    status: str = "active"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def validate(self) -> None:
        if not self.id or not isinstance(self.id, str):
            raise ValueError("Record id must be a non-empty string.")
        if not self.title or not self.title.strip():
            raise ValueError("Record title cannot be empty.")
        if self.priority not in {"low", "medium", "high", "critical"}:
            raise ValueError(f"Invalid priority: {self.priority}")


class DataPipeline:
    """Manages record ingestion, processing, and query operations."""

    def __init__(self, name: str = "my-git") -> None:
        self.name = name
        self._records: dict[str, Record] = {}

    def add_record(self, record: Record) -> Record:
        record.validate()
        if record.id in self._records:
            raise ValueError(f"Record with id '{record.id}' already exists.")
        self._records[record.id] = record
        return record

    def get_record(self, record_id: str) -> Optional[Record]:
        return self._records.get(record_id)

    def filter_by_priority(self, priority: str) -> list[Record]:
        return [r for r in self._records.values() if r.priority == priority]

    def count(self) -> int:
        return len(self._records)

    def to_json(self) -> str:
        data = {
            "pipeline": self.name,
            "total_records": len(self._records),
            "records": [
                {
                    "id": r.id,
                    "title": r.title,
                    "priority": r.priority,
                    "status": r.status,
                    "metadata": r.metadata,
                    "created_at": r.created_at,
                }
                for r in self._records.values()
            ],
        }
        return json.dumps(data, indent=2)


def main() -> None:
    print(f"Initializing my-git data pipeline...")
    pipeline = DataPipeline()
    sample = Record(id="rec-001", title="Initial System Verification", priority="high")
    pipeline.add_record(sample)
    print(f"Successfully processed {pipeline.count()} record(s).")
    print(pipeline.to_json())


if __name__ == "__main__":
    main()
