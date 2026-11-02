import base64
from typing import Any

import httpx

DEMO_TOKEN = "demo-github-token"
DEMO_TOKENS = {"demo-github-token", "demo", "demo-developer"}

DEMO_USER: dict[str, Any] = {
    "id": 999999,
    "login": "demo-developer",
    "name": "Demo Developer",
    "email": "demo@gitauto.ai",
    "avatar_url": "https://avatars.githubusercontent.com/u/999999?v=4",
    "html_url": "https://github.com/demo-developer",
    "public_repos": 14,
    "followers": 42,
    "following": 18,
    "created_at": "2024-01-15T10:00:00Z",
}

DEMO_REPOSITORIES: list[dict[str, Any]] = [
    {
        "id": 1001,
        "name": "sample-python-app",
        "full_name": "demo-developer/sample-python-app",
        "owner": {"login": "demo-developer", "id": 999999},
        "description": "FastAPI + Pytest demo microservice for GitAuto AI testing",
        "default_branch": "main",
        "visibility": "public",
        "private": False,
        "language": "Python",
        "html_url": "https://github.com/demo-developer/sample-python-app",
        "permissions": {"admin": True, "push": True, "pull": True},
    },
    {
        "id": 1002,
        "name": "fullstack-platform",
        "full_name": "demo-developer/fullstack-platform",
        "owner": {"login": "demo-developer", "id": 999999},
        "description": "Next.js + TypeScript web application with automated CI/CD",
        "default_branch": "main",
        "visibility": "public",
        "private": False,
        "language": "TypeScript",
        "html_url": "https://github.com/demo-developer/fullstack-platform",
        "permissions": {"admin": True, "push": True, "pull": True},
    },
    {
        "id": 1003,
        "name": "data-pipeline",
        "full_name": "demo-developer/data-pipeline",
        "owner": {"login": "demo-developer", "id": 999999},
        "description": "Async data processor and task queue worker",
        "default_branch": "main",
        "visibility": "private",
        "private": True,
        "language": "Python",
        "html_url": "https://github.com/demo-developer/data-pipeline",
        "permissions": {"admin": True, "push": True, "pull": True},
    },
]

DEMO_FILES: dict[str, dict[str, str]] = {
    "sample-python-app": {
        "README.md": "# Sample Python App\nA demonstration microservice managed with GitAuto AI.\n",
        "app/main.py": "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/')\ndef read_root():\n    return {'status': 'ok'}\n",
        "tests/test_main.py": "from fastapi.testclient import TestClient\nfrom app.main import app\n\nclient = TestClient(app)\n\ndef test_root():\n    response = client.get('/')\n    assert response.status_code == 200\n",
        "requirements.txt": "fastapi>=0.100.0\nuvicorn>=0.23.0\npytest>=7.0.0\nhttpx>=0.24.0\n",
    },
    "fullstack-platform": {
        "README.md": "# Fullstack Platform\nNext.js frontend application.\n",
        "package.json": '{\n  "name": "fullstack-platform",\n  "version": "1.0.0",\n  "scripts": {\n    "build": "next build",\n    "test": "jest"\n  }\n}\n',
    },
    "data-pipeline": {
        "README.md": "# Data Pipeline\nAsync data processor.\n",
        "pipeline.py": "def run():\n    print('pipeline processing...')\n",
    },
}

DEMO_REFS: dict[str, str] = {}


class GitHubError(Exception):
    def __init__(self, message: str, status_code: int = 502) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class GitHubClient:
    base_url = "https://api.github.com"

    def __init__(self, access_token: str, http_client: httpx.AsyncClient | None = None) -> None:
        self.access_token = access_token
        self.http_client = http_client
        self.is_demo = (access_token in DEMO_TOKENS)

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        client = self.http_client or httpx.AsyncClient(base_url=self.base_url, timeout=15)
        close_client = self.http_client is None
        try:
            response = await client.request(method, path, headers=headers, **kwargs)
            if response.status_code >= 400:
                status = response.status_code if response.status_code in (401, 403, 404, 409, 422) else 502
                gh_msg = ""
                try:
                    payload = response.json()
                    if isinstance(payload, dict) and payload.get("message"):
                        gh_msg = str(payload["message"])
                except Exception:
                    pass

                if status == 403:
                    if gh_msg:
                        detail = f"GitHub rejected the request (HTTP 403: {gh_msg}). If using a Fine-Grained Token, ensure 'Contents' and 'Pull requests' are set to 'Read and write'."
                    else:
                        detail = "GitHub rejected the request (HTTP 403: Forbidden). Please ensure your GitHub token has write permissions ('repo' for classic tokens, or 'Contents: Read and write' and 'Pull requests: Read and write' for fine-grained tokens)."
                elif gh_msg:
                    detail = f"GitHub rejected the request (HTTP {response.status_code}): {gh_msg}"
                else:
                    detail = f"GitHub rejected the request (HTTP {response.status_code})."
                raise GitHubError(detail, status)
            return response.json()
        except httpx.HTTPError as exc:
            raise GitHubError("GitHub could not be reached.") from exc
        finally:
            if close_client:
                await client.aclose()

    async def exchange_code(self, client_id: str, client_secret: str, code: str, redirect_uri: str) -> dict[str, Any]:
        client = self.http_client or httpx.AsyncClient(timeout=15)
        close_client = self.http_client is None
        try:
            response = await client.post(
                "https://github.com/login/oauth/access_token",
                data={"client_id": client_id, "client_secret": client_secret, "code": code, "redirect_uri": redirect_uri},
                headers={"Accept": "application/json"},
            )
            if response.status_code >= 400:
                raise GitHubError("GitHub authorization failed.")
            data = response.json()
            if not data.get("access_token"):
                raise GitHubError("GitHub did not return an access token.", 401)
            return data
        except httpx.HTTPError as exc:
            raise GitHubError("GitHub authorization could not be completed.") from exc
        finally:
            if close_client:
                await client.aclose()

    async def current_user(self) -> dict[str, Any]:
        if self.is_demo:
            return DEMO_USER
        return await self._request("GET", "/user")

    async def repositories(self, page: int, per_page: int, search: str = "") -> list[dict[str, Any]]:
        if self.is_demo:
            repos = DEMO_REPOSITORIES
            if search:
                term = search.casefold()
                repos = [r for r in repos if term in r["full_name"].casefold()]
            start = (page - 1) * per_page
            return repos[start : start + per_page]

        params = {"page": page, "per_page": per_page, "sort": "updated", "direction": "desc"}
        data = await self._request("GET", "/user/repos", params=params)
        if search:
            term = search.casefold()
            data = [item for item in data if term in item.get("full_name", "").casefold()]
        return data

    async def repository(self, repository_id: int) -> dict[str, Any]:
        if self.is_demo:
            for repo in DEMO_REPOSITORIES:
                if repo.get("id") == repository_id:
                    return repo
            raise GitHubError("The repository is not available to this GitHub account.", 404)

        repos = await self._request("GET", "/user/repos", params={"per_page": 100})
        for repo in repos:
            if repo.get("id") == repository_id:
                return repo
        raise GitHubError("The repository is not available to this GitHub account.", 404)

    async def commit(self, owner: str, name: str, ref: str) -> dict[str, Any]:
        if self.is_demo:
            sha = ref if len(ref) == 40 else "a1b2c3d4e5f67890123456789abcdef012345678"
            return {
                "sha": sha,
                "commit": {
                    "message": "feat: initial service setup",
                    "tree": {"sha": "demo-tree-sha-123456"},
                    "author": {"name": "Demo Developer", "email": "demo@gitauto.ai"},
                },
                "stats": {
                    "total": 14,
                    "additions": 12,
                    "deletions": 2,
                },
                "files": [
                    {
                        "filename": "README.md",
                        "status": "modified",
                        "additions": 12,
                        "deletions": 2,
                        "changes": 14,
                    }
                ],
            }
        return await self._request("GET", f"/repos/{owner}/{name}/commits/{ref}")

    async def tree(self, owner: str, name: str, ref: str) -> dict[str, Any]:
        if self.is_demo:
            repo_files = DEMO_FILES.get(name, DEMO_FILES["sample-python-app"])
            return {
                "sha": "demo-tree-sha-123456",
                "tree": [
                    {
                        "path": path,
                        "mode": "100644",
                        "type": "blob",
                        "sha": f"demo-blob-{i}",
                        "size": len(content.encode("utf-8")),
                    }
                    for i, (path, content) in enumerate(repo_files.items())
                ],
            }
        return await self._request("GET", f"/repos/{owner}/{name}/git/trees/{ref}", params={"recursive": "1"})

    async def file(self, owner: str, name: str, path: str, ref: str) -> dict[str, Any]:
        if self.is_demo:
            repo_files = DEMO_FILES.get(name, DEMO_FILES["sample-python-app"])
            content = repo_files.get(path)
            if content is None:
                raise GitHubError(f"File {path} not found in repository.", 404)
            return {
                "encoding": "base64",
                "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
                "size": len(content.encode("utf-8")),
                "path": path,
            }
        return await self._request("GET", f"/repos/{owner}/{name}/contents/{path}", params={"ref": ref})

    async def is_repository_empty(self, owner: str, name: str, default_branch: str = "main") -> bool:
        """Check if a repository has zero commits on its default branch."""
        if self.is_demo:
            return False
        try:
            await self._request("GET", f"/repos/{owner}/{name}/commits/{default_branch}")
            return False
        except GitHubError as exc:
            if exc.status_code in (404, 409):
                return True
            raise

    async def create_or_update_file_contents(
        self,
        owner: str,
        name: str,
        path: str,
        content: str,
        message: str,
        branch: str | None = None,
        sha: str | None = None,
    ) -> dict[str, Any]:
        """Create or update a file via the GitHub Contents API.

        This endpoint automatically bootstraps empty repositories (0 commits),
        creating the initial commit and default branch in a single request.
        """
        if self.is_demo:
            DEMO_FILES.setdefault(name, {})[path] = content
            return {
                "content": {"path": path, "sha": "demo-file-sha"},
                "commit": {"sha": "demo-init-commit-sha", "message": message},
            }

        encoded_content = base64.b64encode(content.encode("utf-8")).decode("ascii")
        payload: dict[str, Any] = {
            "message": message,
            "content": encoded_content,
        }
        if branch:
            payload["branch"] = branch.replace("refs/heads/", "").replace("refs/", "")
        if sha:
            payload["sha"] = sha

        return await self._request("PUT", f"/repos/{owner}/{name}/contents/{path}", json=payload)

    async def ref(self, owner: str, name: str, branch: str) -> str | None:
        clean_branch = branch.replace("refs/heads/", "").replace("refs/", "")
        if self.is_demo:
            if clean_branch in ("main", "master"):
                return "a1b2c3d4e5f67890123456789abcdef012345678"
            return DEMO_REFS.get(f"{owner}/{name}/{clean_branch}", "b2c3d4e5f6a17890123456789abcdef012345678")

        try:
            data = await self._request("GET", f"/repos/{owner}/{name}/git/ref/heads/{clean_branch}")
        except GitHubError as exc:
            if exc.status_code in (404, 409):
                return None
            raise
        return str(data["object"]["sha"])

    async def create_blob(self, owner: str, name: str, content: str) -> str:
        if self.is_demo:
            return "demo-created-blob-sha"
        data = await self._request("POST", f"/repos/{owner}/{name}/git/blobs", json={"content": content, "encoding": "utf-8"})
        return str(data["sha"])

    async def create_tree(self, owner: str, name: str, base_sha: str, entries: list[dict[str, Any]]) -> str:
        if self.is_demo:
            return "demo-created-tree-sha"
        data = await self._request("POST", f"/repos/{owner}/{name}/git/trees", json={"base_tree": base_sha, "tree": entries})
        return str(data["sha"])

    async def create_commit(self, owner: str, name: str, message: str, tree_sha: str, parent_sha: Any) -> dict[str, Any]:
        if self.is_demo:
            return {"sha": "b2c3d4e5f6a17890123456789abcdef012345678", "message": message}
        parents = [parent_sha] if isinstance(parent_sha, str) else list(parent_sha)
        return await self._request("POST", f"/repos/{owner}/{name}/git/commits", json={
            "message": message, "tree": tree_sha, "parents": parents,
        })

    async def create_ref(self, owner: str, name: str, branch: str, commit_sha: str) -> dict[str, Any]:
        clean_branch = branch.replace("refs/heads/", "").replace("refs/", "")
        if self.is_demo:
            DEMO_REFS[f"{owner}/{name}/{clean_branch}"] = commit_sha
            return {"ref": f"refs/heads/{clean_branch}", "sha": commit_sha}
        return await self._request("POST", f"/repos/{owner}/{name}/git/refs", json={
            "ref": f"refs/heads/{clean_branch}", "sha": commit_sha,
        })

    async def update_ref(self, owner: str, name: str, branch: str, commit_sha: str, force: bool = True) -> dict[str, Any]:
        clean_branch = branch.replace("refs/heads/", "").replace("refs/", "")
        if self.is_demo:
            DEMO_REFS[f"{owner}/{name}/{clean_branch}"] = commit_sha
            return {"ref": f"refs/heads/{clean_branch}", "sha": commit_sha}
        return await self._request("PATCH", f"/repos/{owner}/{name}/git/refs/heads/{clean_branch}", json={
            "sha": commit_sha, "force": force,
        })

    async def create_pull_request(
        self, owner: str, name: str, title: str, head: str, base: str, body: str
    ) -> dict[str, Any]:
        if self.is_demo:
            return {
                "id": 101,
                "number": 1,
                "title": title,
                "html_url": f"https://github.com/{owner}/{name}/pull/1",
                "state": "open",
                "head": {"ref": head},
                "base": {"ref": base},
                "body": body,
            }
        return await self._request(
            "POST",
            f"/repos/{owner}/{name}/pulls",
            json={
                "title": title,
                "head": head,
                "base": base,
                "body": body,
            },
        )

    async def pull_requests(
        self, owner: str, name: str, head: str | None = None, state: str = "open"
    ) -> list[dict[str, Any]]:
        if self.is_demo:
            return [
                {
                    "id": 101,
                    "number": 1,
                    "title": "feat: apply approved task changes",
                    "html_url": f"https://github.com/{owner}/{name}/pull/1",
                    "state": "open",
                    "head": {"ref": head or "gitauto-task-1"},
                    "base": {"ref": "main"},
                }
            ]
        params: dict[str, Any] = {"state": state}
        if head:
            params["head"] = head
        return await self._request("GET", f"/repos/{owner}/{name}/pulls", params=params)
