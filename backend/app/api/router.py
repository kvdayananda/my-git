from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.repositories import router as repositories_router
from app.api.analyses import router as analyses_router
from app.api.tasks import router as tasks_router
from app.api.test_runs import router as test_runs_router
from app.api.releases import router as releases_router
from app.api.dashboard import router as dashboard_router
from app.api.jobs import router as jobs_router
from app.api.backup import router as backup_router
from app.api.profile import router as profile_router
from app.api.automation import router as automation_router
from app.api.analytics import router as analytics_router
from app.core.config import get_settings

router = APIRouter(prefix="/api/v1")
router.include_router(auth_router)
router.include_router(profile_router)
router.include_router(repositories_router)
router.include_router(analyses_router)
router.include_router(tasks_router)
router.include_router(test_runs_router)
router.include_router(releases_router)
router.include_router(dashboard_router)
router.include_router(jobs_router)
router.include_router(backup_router)
router.include_router(automation_router)
router.include_router(analytics_router)


@router.get("/status", tags=["system"])
async def api_status() -> dict[str, str]:
    settings = get_settings()
    return {"application": settings.app_name, "environment": settings.app_env}
