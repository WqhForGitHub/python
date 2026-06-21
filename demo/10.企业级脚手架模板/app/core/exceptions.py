"""自定义异常 + 全局异常处理。"""

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppException(Exception):
    """业务异常基类。"""

    def __init__(
        self, message: str, code: str = "BUSINESS_ERROR", status_code: int = 400
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppException):
    def __init__(self, message: str = "资源不存在"):
        super().__init__(
            message, code="NOT_FOUND", status_code=status.HTTP_404_NOT_FOUND
        )


class ConflictError(AppException):
    def __init__(self, message: str = "资源冲突"):
        super().__init__(message, code="CONFLICT", status_code=status.HTTP_409_CONFLICT)


class AuthError(AppException):
    def __init__(self, message: str = "认证失败"):
        super().__init__(
            message, code="AUTH_ERROR", status_code=status.HTTP_401_UNAUTHORIZED
        )


class PermissionDeniedError(AppException):
    def __init__(self, message: str = "权限不足"):
        super().__init__(
            message, code="PERMISSION_DENIED", status_code=status.HTTP_403_FORBIDDEN
        )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def handle_app_exception(_: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "message": exc.message},
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation(_: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "code": "VALIDATION_ERROR",
                "message": "参数校验失败",
                "details": exc.errors(),
            },
        )

    @app.exception_handler(HTTPException)
    async def handle_http(_: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": "HTTP_ERROR", "message": str(exc.detail)},
        )
