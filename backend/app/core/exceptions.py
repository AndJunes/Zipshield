class AppError(Exception):
    """Base class for known, expected application errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class NotFoundError(AppError):
    """Raised when a requested resource does not exist (maps to HTTP 404)."""


class ConflictError(AppError):
    """Raised when a resource clashes with an existing one (maps to HTTP 409)."""
