"""Application errors that are safe to show to a shopkeeper."""


class AppError(Exception):
    def __init__(self, code: str, message: str, status: int = 400, details: list | None = None):
        self.code = code
        self.message = message
        self.status = status
        self.details = details or []
        super().__init__(message)
