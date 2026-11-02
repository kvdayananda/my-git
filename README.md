# GitAuto AI

GitAuto AI is a security-focused development assistant for existing GitHub
repositories. A user explicitly authorizes and selects a repository; the
application then analyzes it, proposes reviewable changes, runs approved
validation in isolation, and only publishes changes after approval.

The project is intentionally being built in phases. The current workspace
contains the Phase 1 foundation and Phase 2 GitHub integration. Live OAuth
requires developer-provided GitHub credentials configured in `.env`.

## Architecture

```text
frontend/          Next.js application and reusable dashboard UI
backend/           FastAPI API, domain services, persistence, and workers
  app/
    api/            HTTP routes and request dependencies
    core/           settings, security, logging, and request context
    db/             SQLAlchemy models, sessions, and Alembic migrations
    integrations/   GitHub and OpenAI adapters
    services/       repository, planning, testing, Git, and analytics logic
    workers/        Celery tasks and scheduling
    main.py         FastAPI application entry point
  tests/            backend unit and integration tests
infra/              local and deployment infrastructure
docs/               architecture and operational documentation
```

The backend owns authorization and all external credentials. The frontend
never receives GitHub tokens, OpenAI keys, or secret file contents. Repository
content is treated as untrusted input, and code execution will be isolated
from the API process before that feature is enabled.

## Local prerequisites

- Python 3.11 or newer
- Node.js 20 or newer
- Docker Desktop
- A manually created GitHub repository for later integration testing

## Initial setup (Windows PowerShell)

```powershell
Copy-Item .env.example .env
docker compose up -d postgres redis

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip

Set-Location frontend
npm install
Set-Location ..
```

Install backend dependencies with `python -m pip install -r backend\requirements.txt`.
Install frontend dependencies with `Set-Location frontend; npm install`.
Do not place real credentials in `.env.example`.

## Development commands

```powershell
# Backend
Set-Location backend
python -m uvicorn app.main:app --reload --port 8000

# Frontend (another terminal)
Set-Location frontend
npm run dev

# Backend tests
Set-Location backend
python -m pytest

# Frontend type check
Set-Location frontend
npm run lint
```

Phase 3 adds bounded repository inspection and an authenticated analysis
workspace. Connected repositories can be inspected at their current default
branch commit through the GitHub Contents and Git Trees APIs. Generated
artifacts are excluded (`node_modules`, `.next`, build caches, virtual
environments, vendor directories, and coverage), as are environment files and
private-key extensions. File count, file size, and model-context limits are
configurable in the backend settings. Repository code is never executed.

The analysis API includes:

- `POST /api/v1/analyses/repositories/{repository_id}/analyze`
- `GET /api/v1/analyses/repositories/{repository_id}/analysis/latest`
- `GET /api/v1/analyses/{analysis_id}`

Analysis records are associated with the inspected commit SHA. Deterministic
inspection remains available without an OpenAI key; set `OPENAI_API_KEY` and
optionally `OPENAI_MODEL` in the backend `.env` to add validated model
enrichment. The key stays server-side and repository files are treated as
untrusted input. Run `python -m alembic upgrade head` from `backend` after
configuring the database. AI, scheduling, analytics, and publishing views
outside the analysis workspace remain development status surfaces.

Phase 4 adds an authenticated development-task workflow. Tasks are tied to a
connected repository and the latest analyzed commit, receive an explicit plan
approval step, and use per-user/per-task workspace directories under
`WORKSPACE_ROOT`. Generated paths reject traversal, absolute paths, protected
files, and credential-like values. The workflow never commits or pushes.

Phase 4 task endpoints include:

- `POST /api/v1/development-tasks/repositories/{repository_id}`
- `GET /api/v1/development-tasks`
- `POST /api/v1/development-tasks/{task_id}/plan`
- `POST /api/v1/development-tasks/{task_id}/plan/approve`
- `POST /api/v1/development-tasks/{task_id}/generate`
- `POST /api/v1/development-tasks/{task_id}/review/approve`
- `POST /api/v1/development-tasks/{task_id}/review/reject`
- `POST /api/v1/development-tasks/{task_id}/revision`
- `POST /api/v1/development-tasks/{task_id}/cancel`

OpenAI generation is enabled when `OPENAI_API_KEY` is configured. Test
execution uses the configured Docker sandbox when the daemon and image are
available; otherwise it is reported as unavailable rather than executed in the
FastAPI process. Configure
a restricted non-root container runner with filesystem, CPU, memory, disk,
network, timeout, and secret-isolation controls before enabling those stages.
Generation also honors `OPENAI_TIMEOUT_SECONDS` and
`OPENAI_MAX_OUTPUT_TOKENS`; no API key is sent to the frontend.

Phase 5B adds a fail-closed sandbox runner. The configured local image is
`gitauto-ai-sandbox:local`. The supported profile is
`python-pytest`, using a prebuilt image, no network, a read-only container
root, dropped capabilities, non-root UID, bounded CPU/memory/PIDs/tmpfs, and
bounded output. The runner never accepts a command or host path from the
frontend. Build the image from [infrastructure/sandbox/Dockerfile](infrastructure/sandbox/Dockerfile)
and pin its base-image digest before production deployment. The local image was
verified with Docker Desktop Linux engine during development. Docker daemon
availability is checked at runtime; when Docker or the image is unavailable,
the test result is `unavailable`, never `passed`. Repository dependencies are
not installed automatically and JavaScript/other language profiles are not
enabled until reviewed images and policies exist.

Phase 5C adds an approval-gated release workflow. A successful sandbox run is
bound to a deterministic candidate hash covering the generated operations and
contents. The release API records the exact base commit, approved paths,
target/default branch, candidate branch, test run, secret-scan result, and
approval. Before release it rechecks the remote default branch, candidate
immutability, branch availability, ownership, and the persisted sandbox result.
It creates a commit through GitHub's Git Database API and creates only a
dedicated `gitauto/task-<task-id>-<short-id>` branch; it never force-pushes or
writes the default branch. The candidate must be explicitly approved after
the readiness checks pass.

Release endpoints include:

- `POST /api/v1/release-candidates/tasks/{task_id}`
- `GET /api/v1/release-candidates/{candidate_id}`
- `GET /api/v1/release-candidates/{candidate_id}/audit`
- `POST /api/v1/release-candidates/{candidate_id}/approve`
- `POST /api/v1/release-candidates/{candidate_id}/release`

Live GitHub write behavior requires an OAuth token with repository write
permission and remains unverified without an authorized test repository.
Automated tests use mocked provider responses and never push to a production
repository. If a remote operation is interrupted after commit creation, the
candidate remains in a recoverable state with the commit SHA persisted; a
retry verifies the remote branch before completing the release.

Release concurrency uses a database compare-and-set transition from
`approved` to `releasing` with a persisted five-minute lease. This works with
the configured SQLite database and with transactional server databases,
without holding a transaction open during GitHub requests. Expired leases
can be reclaimed after remote-state inspection. If commit creation itself is
ambiguous, the candidate is marked `ambiguous` and automatic retry is blocked,
because GitHub's Git Database API does not provide an idempotency key for
commit creation. If a commit SHA was persisted before an ambiguous branch
request, retries inspect the branch and reuse that commit rather than creating
another one.

`npm install` currently reports upstream advisories in Next.js's transitive
PostCSS dependency. The available automatic fix requires a breaking Next.js
major upgrade, so it has not been applied in this foundation phase.

## Planned implementation phases

1. Architecture and environment foundation
2. Frontend design system and dashboard shell (in progress)
3. FastAPI application, database models, and migrations
4. Secure GitHub authentication and repository access (implemented; awaiting credentials for live verification)
5. Repository analysis and AI development planning
6. Reviewable changes, isolated testing, and safe Git operations
7. Celery scheduling, analytics, activity logs, deployment, and security tests

## Security boundaries

- Repositories are selected by the user; the application never creates one.
- There are no fake success responses or fabricated contribution metrics.
- Pushes require explicit approval by default.
- Secret files, credentials, private keys, dependency caches, and generated
  artifacts are excluded from model context.
- No production credential is required for ordinary local tests.

See [docs/architecture.md](docs/architecture.md) for the initial component
boundaries and data flow.

See [docs/github-integration.md](docs/github-integration.md) for OAuth
registration, callback configuration, migration, and security instructions.
