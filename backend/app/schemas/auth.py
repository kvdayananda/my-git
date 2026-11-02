from pydantic import BaseModel, ConfigDict


class AuthenticatedUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    github_id: int
    login: str
    name: str | None = None
    email: str | None = None
    custom_display_name: str | None = None
    display_name: str | None = None
    avatar_url: str | None = None


class AuthStatus(BaseModel):
    authenticated: bool
    user: AuthenticatedUser | None = None


class PatLoginRequest(BaseModel):
    token: str
