class AppException(Exception):
    def __init__(self, message: str, status_code: int, code: str) -> None:
        self.message = message
        self.status_code = status_code
        self.code = code
        super().__init__(message)


class BadRequestError(AppException):
    def __init__(self, message: str) -> None:
        super().__init__(message, 400, "BAD_REQUEST")


class UnauthorizedError(AppException):
    def __init__(self, message: str = "Not authenticated") -> None:
        super().__init__(message, 401, "UNAUTHORIZED")


class ForbiddenError(AppException):
    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(message, 403, "FORBIDDEN")


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, 404, "NOT_FOUND")


class ConflictError(AppException):
    def __init__(self, message: str) -> None:
        super().__init__(message, 409, "CONFLICT")
