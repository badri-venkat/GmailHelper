from enum import Enum


class Reason(Enum):
    BAD_REQUEST = "BAD_REQUEST"
    ENTITY_NOT_FOUND = "ENTITY_NOT_FOUND"
    MISSING_PARAMS = "MISSING_PARAMS"
    UNAUTHORIZED = "UNAUTHORIZED"
    EXECUTION_ERROR = "EXECUTION_ERROR"
    INVALID_PARAM = "INVALID_PARAM"
    NOT_PROCESSED = "NOT_PROCESSED"
    MISSING_DATA = "MISSING_DATA"
    INVALID_DATA = "INVALID_DATA"
    CONFLICT = "CONFLICT"


class ServiceException(Exception):
    def __init__(self, reason: Reason, message: str):
        super().__init__(message)
        self.reason = reason
        self.message = message

    def get_code(self) -> Reason:
        return self.reason

    def get_message(self) -> str:
        return self.message
