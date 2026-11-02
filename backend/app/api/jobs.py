from fastapi import APIRouter, Depends

from app.api.auth import current_user
from app.core.config import get_settings
from app.db.models import User
from app.workers.celery_app import celery_app

router = APIRouter(prefix="/jobs", tags=["worker jobs"])


@router.get("/health")
def worker_health() -> dict[str, object]:
    settings = get_settings()
    return {
        "status": "ready",
        "broker_configured": bool(settings.redis_url),
        "task_always_eager": settings.celery_task_always_eager,
    }


@router.get("/{job_id}")
def get_job_status(job_id: str, user: User = Depends(current_user)) -> dict[str, object]:
    try:
        res = celery_app.AsyncResult(job_id)
        state = res.state
        ready = res.ready()
        successful = res.successful() if ready else False
        failed = res.failed() if ready else False
        result_data = None
        if ready:
            try:
                result_data = res.result if not isinstance(res.result, Exception) else str(res.result)
            except Exception as exc:
                result_data = str(exc)

        return {
            "job_id": job_id,
            "state": state,
            "ready": ready,
            "successful": successful,
            "failed": failed,
            "result": result_data,
        }
    except Exception as exc:
        return {
            "job_id": job_id,
            "state": "PENDING",
            "ready": False,
            "successful": False,
            "failed": False,
            "result": None,
            "notice": "Worker result storage is in local or eager mode.",
        }
