# GitHub integration

GitAuto AI uses a GitHub OAuth application for account identity and repository
access. The browser receives only a secure, HttpOnly application session
cookie. GitHub access tokens are encrypted before persistence and are never
returned to frontend JavaScript or API responses.

## Register the OAuth application

1. In GitHub, open **Settings → Developer settings → OAuth Apps → New OAuth App**.
2. Set the local homepage URL to `http://localhost:3000`.
3. Set the authorization callback URL to
   `http://localhost:8000/api/v1/auth/github/callback`.
4. Copy the generated client ID and client secret into the local `.env` file.

The application requests `read:user user:email repo`. The `repo` scope is
required to list private repositories and inspect write permissions. GitHub
organization policies may still restrict access.

## Configuration

Required local values:

```text
APP_SECRET_KEY=<long random value>
GITHUB_CLIENT_ID=<OAuth client ID>
GITHUB_CLIENT_SECRET=<OAuth client secret>
GITHUB_REDIRECT_URI=http://localhost:8000/api/v1/auth/github/callback
FRONTEND_URL=http://localhost:3000
DATABASE_URL=sqlite:///./gitauto.db
```

In production, use a managed PostgreSQL database, a secret manager for the
application secret, HTTPS callback URLs, and secure cookies. The encrypted
GitHub token data requires the same `APP_SECRET_KEY` to decrypt; rotate it
through a deliberate credential re-encryption procedure rather than deleting
it casually.

## Local flow

```powershell
Copy-Item .env.example .env
# Edit .env with OAuth values and a random APP_SECRET_KEY
Set-Location backend
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --port 8000
```

Open `http://localhost:3000`, select **Connect GitHub**, and approve the OAuth
request. Denied consent, invalid state, missing configuration, and GitHub API
failures are surfaced without exposing credentials.

## Phase boundary

This phase supports identity, repository listing, metadata, permission
display, and explicit repository connections. It does not clone, modify,
commit, or push repository code. Those actions require later review, sandbox,
and approval workflows.
