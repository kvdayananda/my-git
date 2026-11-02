import asyncio
import json
import logging
from pathlib import Path

from sqlalchemy import select

from app.core.config import get_settings
from app.db.base import utc_now
from app.db.models import (
    Analysis,
    DevelopmentTask,
    GitHubConnection,
    ProposedChange,
    RepositoryConnection,
    TaskEvent,
    TestRun,
)
from app.db.session import SessionLocal
from app.services.analysis import (
    ModelReport,
    deterministic_report,
    enrich_with_openai,
    inspect_repository,
)
from app.services.code_generation import (
    GenerationError,
    apply_changes,
    generate_changes,
)
from app.services.github.client import GitHubClient, GitHubError
from app.services.sandbox_manager import SandboxUnavailable, run_in_sandbox
from app.services.sandbox_policy import available_profiles
from app.services.security import decrypt_token
from app.schemas.task import Plan
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    return asyncio.run(coro)


@celery_app.task(bind=True, name="app.workers.tasks.analyze_repository_task")
def analyze_repository_task(self, analysis_id: int, user_id: int) -> dict[str, object]:
    logger.info("Executing analyze_repository_task analysis_id=%s user_id=%s", analysis_id, user_id)
    settings = get_settings()

    with SessionLocal() as db:
        analysis = db.get(Analysis, analysis_id)
        if analysis is None or analysis.user_id != user_id:
            logger.error("Analysis not found analysis_id=%s", analysis_id)
            return {"status": "error", "message": "Analysis record not found."}

        connection = db.get(RepositoryConnection, analysis.repository_connection_id)
        github_conn = db.scalar(select(GitHubConnection).where(GitHubConnection.user_id == user_id))

        if connection is None or github_conn is None:
            analysis.status = "failed"
            analysis.completed_at = utc_now()
            db.commit()
            return {"status": "error", "message": "Repository or GitHub credentials unavailable."}

        async def _do_analysis():
            client = GitHubClient(decrypt_token(github_conn.encrypted_access_token))
            inspection = await inspect_repository(
                client, connection.owner, connection.name, connection.default_branch, settings
            )
            summary, findings, recommendations, plan = deterministic_report(inspection)
            deterministic = ModelReport(
                project_summary=summary,
                detected_technologies=inspection.technologies,
                findings=findings,
                recommendations=recommendations,
                development_plan=plan,
                limitations=inspection.limitations,
            )
            ai_report, token_usage = await enrich_with_openai(inspection, deterministic, settings)
            report = ai_report or deterministic
            limitations = sorted(set(inspection.limitations + report.limitations))
            if settings.openai_api_key and ai_report is None:
                limitations.append("AI enrichment was unavailable; this report contains deterministic inspection results only.")
            return inspection, report, limitations, token_usage, bool(ai_report)

        try:
            inspection, report, limitations, token_usage, has_ai = _run_async(_do_analysis())
            analysis.status = "partial" if limitations else "completed"
            analysis.project_summary = report.project_summary
            analysis.detected_technologies = json.dumps(report.detected_technologies or inspection.technologies)
            analysis.file_inventory = json.dumps([{"path": f.path, "size": f.size, "language": f.language} for f in inspection.files])
            analysis.findings = json.dumps([item.model_dump() for item in report.findings])
            analysis.recommendations = json.dumps(report.recommendations)
            analysis.development_plan = json.dumps([item.model_dump() for item in report.development_plan])
            analysis.limitations = json.dumps(limitations)
            analysis.model_identifier = settings.openai_model if has_ai else None
            analysis.token_usage = token_usage
            analysis.completed_at = utc_now()
            db.commit()
            return {"status": "completed", "analysis_id": analysis_id}
        except Exception as exc:
            logger.exception("Error in analyze_repository_task")
            analysis.status = "failed"
            analysis.limitations = json.dumps([f"Analysis failed: {str(exc)}"])
            analysis.completed_at = utc_now()
            db.commit()
            return {"status": "failed", "error": str(exc)}


@celery_app.task(bind=True, name="app.workers.tasks.generate_code_task")
def generate_code_task(self, task_id: int, user_id: int) -> dict[str, object]:
    logger.info("Executing generate_code_task task_id=%s user_id=%s", task_id, user_id)
    settings = get_settings()

    with SessionLocal() as db:
        task = db.get(DevelopmentTask, task_id)
        if task is None or task.user_id != user_id:
            return {"status": "error", "message": "Task not found."}

        repository = db.get(RepositoryConnection, task.repository_connection_id)
        github_conn = db.scalar(select(GitHubConnection).where(GitHubConnection.user_id == user_id))

        if repository is None or github_conn is None:
            task.status = "failed"
            task.error_summary = "Authorization context is unavailable."
            db.commit()
            return {"status": "failed", "error": task.error_summary}

        async def _do_generation():
            plan = Plan.model_validate_json(task.plan)
            client = GitHubClient(decrypt_token(github_conn.encrypted_access_token))
            generated, token_usage = await generate_changes(
                client=client,
                owner=repository.owner,
                name=repository.name,
                commit_sha=task.base_commit_sha,
                workspace=Path(task.workspace_path).resolve(),
                plan=plan,
                instructions=task.instructions,
                settings=settings,
            )
            return generated, token_usage

        try:
            generated, token_usage = _run_async(_do_generation())
            apply_changes(Path(task.workspace_path).resolve(), generated, settings)

            for change in generated.changes:
                db.add(
                    ProposedChange(
                        development_task_id=task.id,
                        file_path=change.file_path,
                        operation=change.operation,
                        reason=change.reason,
                        proposed_content=change.proposed_content,
                        validation_status="passed",
                        review_status="pending",
                    )
                )
            task.token_usage = token_usage
            task.status = "awaiting_review"
            task.validation_results = json.dumps([{"status": "passed", "detail": "Structured changes and protected-path checks passed."}])
            task.test_results = json.dumps([{"status": "not_run", "detail": "Tests are not run by the API process."}])
            task.error_summary = None
            db.add(TaskEvent(development_task_id=task.id, event_type="generation_succeeded", sanitized_details=json.dumps({"changes": str(len(generated.changes))})))
            db.commit()
            return {"status": "completed", "task_id": task_id, "changes_count": len(generated.changes)}
        except Exception as exc:
            logger.exception("Error in generate_code_task")
            task.status = "failed"
            task.error_summary = str(exc)
            task.test_results = json.dumps([{"status": "not_run", "detail": "Generation failed before tests could run."}])
            db.add(TaskEvent(development_task_id=task.id, event_type="generation_failed", sanitized_details=json.dumps({"error": str(exc)})))
            db.commit()
            return {"status": "failed", "error": str(exc)}


@celery_app.task(bind=True, name="app.workers.tasks.run_sandbox_test_task")
def run_sandbox_test_task(self, test_run_id: int, user_id: int) -> dict[str, object]:
    logger.info("Executing run_sandbox_test_task test_run_id=%s user_id=%s", test_run_id, user_id)
    settings = get_settings()

    with SessionLocal() as db:
        run = db.get(TestRun, test_run_id)
        if run is None or run.user_id != user_id:
            return {"status": "error", "message": "TestRun not found."}

        task = db.get(DevelopmentTask, run.development_task_id)
        if task is None:
            run.status = "infrastructure_error"
            run.summary = "Linked development task not found."
            db.commit()
            return {"status": "error", "message": run.summary}

        profile = available_profiles(Path(task.workspace_path), settings)[0]
        if not profile["available"]:
            run.status = "unavailable"
            run.error_details = str(profile["reason"])
            run.summary = "Sandbox execution is unavailable."
            db.commit()
            return {"status": "unavailable", "reason": run.error_details}

        run.status = "running"
        db.commit()

        try:
            result = _run_async(run_in_sandbox(Path(task.workspace_path), "python-pytest", settings))
            run.status = str(result["status"])
            run.exit_code = result["exit_code"]  # type: ignore[assignment]
            run.started_at = result["started_at"]  # type: ignore[assignment]
            run.ended_at = result["ended_at"]  # type: ignore[assignment]
            run.duration_ms = result["duration_ms"]  # type: ignore[assignment]
            run.timed_out = bool(result["timed_out"])
            run.stdout = str(result["stdout"])[: settings.sandbox_output_limit_bytes]
            run.stderr = str(result["stderr"])[: settings.sandbox_output_limit_bytes]
            run.summary = str(result["summary"])
            db.commit()
            return {"status": run.status, "test_run_id": test_run_id}
        except SandboxUnavailable as exc:
            run.status = "unavailable"
            run.error_details = str(exc)
            run.summary = "Sandbox execution is unavailable."
            db.commit()
            return {"status": "unavailable", "error": str(exc)}
        except Exception as exc:
            logger.exception("Error in run_sandbox_test_task")
            run.status = "infrastructure_error"
            run.error_details = str(exc)
            run.summary = "Sandbox infrastructure failed."
            db.commit()
            return {"status": "failed", "error": str(exc)}


@celery_app.task(name="app.workers.tasks.dispatch_scheduled_automation_task")
def dispatch_scheduled_automation_task() -> dict[str, object]:
    """Periodic Celery worker task to evaluate and dispatch daily automation schedules."""
    from app.services.automation.scheduler import evaluate_and_dispatch_due_schedules

    logger.info("Executing dispatch_scheduled_automation_task")
    with SessionLocal() as db:
        dispatched = _run_async(evaluate_and_dispatch_due_schedules(db))
        logger.info("dispatch_scheduled_automation_task completed. Dispatched runs: %s", dispatched)
        return {"status": "success", "dispatched_run_ids": dispatched}
