import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exception: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exception.status_code,
            content={"error": {"message": exception.message}},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_: Request, exception: Exception) -> JSONResponse:
        logger.exception("Unhandled application error", exc_info=exception)
        return JSONResponse(
            status_code=500,
            content={"error": {"message": "An unexpected error occurred."}},
        )
