from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas import ErrorBody, ErrorCode, ErrorResponse


class KairosError(Exception):
    def __init__(self, code: ErrorCode, message: str, status_code: int = 400, details: dict | None = None):
        super().__init__(message)
        self.code, self.message, self.status_code, self.details = code, message, status_code, details

    def to_body(self) -> ErrorBody:
        return ErrorBody(code=self.code, message=self.message, details=self.details)


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(KairosError)
    async def _handle_kairos(_: Request, exc: KairosError) -> JSONResponse:
        body = ErrorResponse(error=exc.to_body()).model_dump(mode="json")
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(RequestValidationError)
    async def _handle_validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        body = ErrorResponse(
            error=ErrorBody(
                code=ErrorCode.INTERNAL_ERROR,
                message="Request validation error",
                details={"errors": exc.errors()},
            )
        ).model_dump(mode="json")
        return JSONResponse(status_code=422, content=body)

    @app.exception_handler(StarletteHTTPException)
    async def _handle_http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = ErrorCode.PRESET_NOT_FOUND if exc.status_code == 404 else ErrorCode.INTERNAL_ERROR
        body = ErrorResponse(
            error=ErrorBody(
                code=code,
                message=str(exc.detail),
                details=None,
            )
        ).model_dump(mode="json")
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(Exception)
    async def _handle_unhandled(_: Request, exc: Exception) -> JSONResponse:
        settings = get_settings()
        details = None if settings.app_env == "production" else {"type": exc.__class__.__name__, "detail": str(exc)}
        body = ErrorResponse(
            error=ErrorBody(
                code=ErrorCode.INTERNAL_ERROR,
                message="An unexpected internal error occurred.",
                details=details,
            )
        ).model_dump(mode="json")
        return JSONResponse(status_code=500, content=body)
