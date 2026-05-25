class AppError(Exception):
    """Base application error."""

    def __init__(self, message: str, code: str = "app_error") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class ValidationError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="validation_error")


class NotFoundError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="not_found")


class ParseError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="parse_error")
