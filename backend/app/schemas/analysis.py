from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AnalysisFinding(BaseModel):
    id: str
    category: str
    title: str
    description: str
    severity: Literal["critical", "high", "medium", "low", "info"]
    evidence: str
    affected_paths: list[str] = Field(default_factory=list)
    recommended_action: str
    confidence: float = Field(ge=0, le=1)


class DevelopmentTask(BaseModel):
    id: str
    title: str
    description: str
    priority: Literal["high", "medium", "low"]
    complexity: Literal["small", "medium", "large"]
    relevant_paths: list[str] = Field(default_factory=list)
    reason: str
    acceptance_criteria: list[str] = Field(default_factory=list)
    test_strategy: str
    risks: list[str] = Field(default_factory=list)


class AnalysisReport(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    repository_id: int
    commit_sha: str
    status: Literal["pending", "completed", "partial", "failed"]
    project_summary: str
    detected_technologies: list[str]
    file_inventory: list[dict[str, str | int]]
    findings: list[AnalysisFinding]
    recommendations: list[str]
    development_plan: list[DevelopmentTask]
    limitations: list[str]
    model_identifier: str | None = None
    token_usage: int | None = None
    created_at: datetime
    completed_at: datetime | None = None


class AnalysisStartResponse(BaseModel):
    id: int
    status: str
    commit_sha: str
