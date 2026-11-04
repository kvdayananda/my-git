"""
Unit Test Suite for my-git
Validates core application models, pipeline logic, and error handling.
"""

import pytest
from app.main import DataPipeline, Record


def test_record_creation_and_validation():
    record = Record(id="test-1", title="Sample Record", priority="high")
    record.validate()
    assert record.id == "test-1"
    assert record.title == "Sample Record"
    assert record.priority == "high"


def test_record_validation_empty_title():
    record = Record(id="test-2", title="", priority="medium")
    with pytest.raises(ValueError, match="Record title cannot be empty"):
        record.validate()


def test_record_validation_invalid_priority():
    record = Record(id="test-3", title="Valid Title", priority="urgent")
    with pytest.raises(ValueError, match="Invalid priority"):
        record.validate()


def test_pipeline_add_and_get():
    pipeline = DataPipeline("TestApp")
    record = Record(id="rec-1", title="Task 1", priority="low")
    pipeline.add_record(record)
    assert pipeline.count() == 1
    retrieved = pipeline.get_record("rec-1")
    assert retrieved is not None
    assert retrieved.title == "Task 1"


def test_pipeline_duplicate_prevention():
    pipeline = DataPipeline("TestApp")
    record = Record(id="rec-dup", title="Duplicate Test")
    pipeline.add_record(record)
    with pytest.raises(ValueError, match="already exists"):
        pipeline.add_record(record)


def test_pipeline_filtering():
    pipeline = DataPipeline("TestApp")
    pipeline.add_record(Record(id="1", title="Low 1", priority="low"))
    pipeline.add_record(Record(id="2", title="High 1", priority="high"))
    pipeline.add_record(Record(id="3", title="High 2", priority="high"))

    high_records = pipeline.filter_by_priority("high")
    assert len(high_records) == 2
    assert all(r.priority == "high" for r in high_records)


def test_pipeline_json_serialization():
    pipeline = DataPipeline("TestApp")
    pipeline.add_record(Record(id="json-1", title="Serialization Test", priority="critical"))
    json_output = pipeline.to_json()
    assert "total_records" in json_output
    assert "json-1" in json_output
