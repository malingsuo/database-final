"""
src/core/exceptions.py - 自訂例外與統一錯誤格式
"""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    status_code: int = 500
    code: str = "INTERNAL_ERROR"
    detail: str = "Internal server error"

    def __init__(self, detail: str | None = None, code: str | None = None) -> None:
        self.detail = detail or self.__class__.detail
        self.code = code or self.__class__.code
        super().__init__(self.detail)


class NotFoundException(AppException):
    status_code = 404
    code = "NOT_FOUND"
    detail = "Resource not found"


class UnauthorizedException(AppException):
    status_code = 401
    code = "UNAUTHORIZED"
    detail = "Authentication required"


class ForbiddenException(AppException):
    status_code = 403
    code = "FORBIDDEN"
    detail = "Permission denied"


class ConflictException(AppException):
    status_code = 409
    code = "CONFLICT"
    detail = "Resource already exists"


class BadRequestException(AppException):
    status_code = 400
    code = "BAD_REQUEST"
    detail = "Invalid request"


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": exc.code},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "code": "INTERNAL_ERROR"},
    )
