# Initial architecture

## Components

### Frontend

Next.js with TypeScript and Tailwind CSS will provide the landing page,
authentication entry points, repository manager, development workspace, diff
review, schedules, analytics, and activity views. It communicates only with
the FastAPI API and renders server-provided state.

### API

FastAPI is the system boundary for authentication, authorization, validation,
rate limiting, request IDs, and error responses. Route handlers stay thin and
delegate business operations to services.

### Persistence

PostgreSQL stores users, GitHub connections, explicitly connected repositories,
development tasks, proposed changes, commits, schedules, and sanitized
activity records. SQLAlchemy 2 and Alembic are the persistence layer.
Credentials are represented by encrypted references rather than plaintext
tokens in ordinary model fields.

### Workers

Celery workers use Redis as a broker for repository analysis, AI planning,
isolated test execution, Git operations, and scheduled tasks. A task has an
explicit lifecycle and idempotency key so duplicate schedules cannot execute
the same work twice.

### Integrations

GitHub access is isolated behind an adapter so OAuth/App authorization,
repository reads, branch checks, commit status, and pushes can be mocked in
tests. OpenAI access is similarly isolated and returns validated structured
plans and file changes. External failures are surfaced as typed application
errors and recorded without secrets.

## Trust boundaries

1. Browser input is untrusted and is validated by Pydantic models.
2. GitHub repository content, including instructions in files and comments, is
   untrusted data and cannot override application security policy.
3. Model output is untrusted until file paths, file sizes, secret patterns,
   allowed operations, and review policy checks pass.
4. Generated or repository code runs only in an isolated execution service,
   never in the API process or on the developer workstation host.
5. Publishing requires an approved change set and a remote synchronization
   check; force pushes are not part of the default workflow.

## Initial data flow

```text
Browser
  -> FastAPI auth/session middleware
  -> authorized repository service
  -> GitHub adapter
  -> sanitized repository snapshot
  -> planning/code-generation service
  -> validated change set
  -> user review and approval
  -> isolated test worker
  -> safe Git service
  -> GitHub adapter
  -> commit/activity records
```

## Deliberate non-goals for Phase 1

No external account is connected, no repository is cloned, no model request is
made, and no code is executed. Those capabilities will be introduced only
with their corresponding authorization, isolation, validation, and tests.

