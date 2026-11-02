from pydantic import BaseModel, ConfigDict, Field


class Repository(BaseModel):
    id: int
    name: str
    owner: str
    description: str | None = None
    default_branch: str
    visibility: str
    language: str | None = None
    html_url: str
    can_push: bool = False
    connected: bool = False


class RepositoryPage(BaseModel):
    items: list[Repository]
    page: int
    per_page: int
    has_next: bool


class RepositoryConnectRequest(BaseModel):
    repository_id: int = Field(gt=0)
