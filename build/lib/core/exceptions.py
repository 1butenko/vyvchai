from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base application exception."""

    def __init__(
        self, detail: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        super().__init__(status_code=status_code, detail=detail)


class NotFoundError(AppException):
    """Resource not found."""

    def __init__(self, detail: str = "Resource not found"):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class ValidationError(AppException):
    """Validation error."""

    def __init__(self, detail: str = "Validation failed"):
        super().__init__(
            detail=detail, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class AuthenticationError(AppException):
    """Authentication error."""

    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)


class AuthorizationError(AppException):
    """Authorization error."""

    def __init__(self, detail: str = "Access forbidden"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)


class RateLimitError(AppException):
    """Rate limit exceeded."""

    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(detail=detail, status_code=status.HTTP_429_TOO_MANY_REQUESTS)


class LLMError(AppException):
    """LLM service error."""

    def __init__(self, detail: str = "LLM service error"):
        super().__init__(detail=detail, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


class SolverError(AppException):
    """Solver error."""

    def __init__(self, detail: str = "Failed to solve question"):
        super().__init__(
            detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
