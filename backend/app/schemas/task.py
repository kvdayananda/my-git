from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


TaskType = Literal[
    "feature", "improvement", "bug_fix", "tests", "documentation",
    "refactor", "error_handling", "type_annotations", "analysis_finding",
]
TaskStatus = Literal[
    "queued", "planning", "awaiting_plan_approval", "generating", "validating",
    "awaiting_review", "revision_requested", "approved", "rejected", "failed", "cancelled",
]


class TaskCreate(BaseModel):
    task_type: TaskType
    instructions: str = Field(min_length=1, max_length=10_000)
    analysis_id: int | None = Field(default=None, gt=0)


class Plan(BaseModel):
    summary: str
    objective: str
    files_to_create: list[str] = Field(default_factory=list)
    files_to_modify: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    expected_behavior: str
    acceptance_criteria: list[str] = Field(default_factory=list)
    testing_strategy: str
    risks: list[str] = Field(default_factory=list)


class ProposedChangeResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    file_path: str
    operation: Literal["create", "modify", "delete"]
    reason: str
    proposed_content: str
    validation_status: str
    review_status: str


class TaskResponse(BaseModel):
    id: int
    repository_id: int
    base_commit_sha: str
    task_type: str
    instructions: str
    status: TaskStatus
    plan: Plan | None
    validation_results: list[dict[str, str]]
    test_results: list[dict[str, str]]
    token_usage: int | None
    error_summary: str | None
    changes: list[ProposedChangeResponse]
    created_at: datetime
    completed_at: datetime | None


class RevisionRequest(BaseModel):
    instructions: str = Field(min_length=1, max_length=10_000)


class GeneratedChange(BaseModel):
    model_config = {"extra": "forbid"}

    file_path: str
    operation: Literal["create", "modify", "delete"]
    reason: str = Field(min_length=1, max_length=2_000)
    proposed_content: str = ""
    related_plan_item: str = Field(default="", max_length=500)


class GeneratedChanges(BaseModel):
    model_config = {"extra": "forbid"}

    changes: list[GeneratedChange] = Field(max_length=100)
