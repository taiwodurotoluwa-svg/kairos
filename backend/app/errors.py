from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.schemas import ErrorBody, ErrorCode, ErrorResponse


class KairosError(Exception):
    def __init__(self, code: ErrorCode, message: str, status_code: int = 400, details: dict | None = None):
        super().__init__(message)
        self.code, self.message, self.status_code, self.details = code, message, status_code, details

    def to_body(self) -> ErrorBody:
        return ErrorBody(code=self.code, message=self.message, details=self.details)


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(KairosError)
    async def _handle(_: Request, exc: KairosError) -> JSONResponse:
        body = ErrorResponse(error=exc.to_body()).model_dump(mode="json")
        return JSONResponse(status_code=exc.status_code, content=body)
