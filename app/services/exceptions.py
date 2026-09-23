class ServiceError(Exception):
    """Base exception for all service layer errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ConflictError(ServiceError):
    """Raised when an entity or unique constraint conflict occurs."""

    pass


class NotFoundError(ServiceError):
    """Raised when an entity is not found."""

    pass


class BadRequestError(ServiceError):
    """Raised when a business rule or validation fails."""

    pass


class UnauthorizedError(ServiceError):
    """Raised when authentication credentials fail."""

    pass


class ForbiddenError(ServiceError):
    """Raised when an authenticated entity lacks permission."""

    pass
