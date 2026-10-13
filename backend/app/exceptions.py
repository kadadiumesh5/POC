class PlatformError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code


class NotFoundError(PlatformError):
    def __init__(self, message: str):
        super().__init__(message, 404)


class ConflictError(PlatformError):
    def __init__(self, message: str):
        super().__init__(message, 409)


class ValidationFailure(PlatformError):
    def __init__(self, message: str):
        super().__init__(message, 422)


class AgentError(PlatformError):
    def __init__(self, message: str):
        super().__init__(message, 400)
