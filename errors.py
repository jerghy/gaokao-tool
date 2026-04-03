from typing import Optional, Dict, Any


class AppError(Exception):
    """应用基础异常类"""
    
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)
    
    def to_dict(self) -> dict:
        result = {
            "success": False,
            "error": {
                "code": self.code,
                "message": self.message
            }
        }
        if self.details:
            result["error"]["details"] = self.details
        return result


class ValidationError(AppError):
    """验证错误 (400)"""
    
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=400,
            details=details
        )


class NotFoundError(AppError):
    """资源未找到 (404)"""
    
    def __init__(self, resource: str, identifier: str = None):
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} '{identifier}' not found"
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=404,
            details={"resource": resource, "identifier": identifier}
        )


class ConflictError(AppError):
    """资源冲突 (409)"""
    
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=409,
            details=details
        )


class InternalError(AppError):
    """内部错误 (500)"""
    
    def __init__(self, message: str = "服务器内部错误", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code="INTERNAL_ERROR",
            status_code=500,
            details=details
        )
