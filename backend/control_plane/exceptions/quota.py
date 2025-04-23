from typing import Optional
from uuid import UUID


class QuotaExceededException(Exception):
    """
    Исключение для случаев превышения квоты
    """

    def __init__(
            self,
            quota_type: str,
            user_id: Optional[UUID] = None,
            requested_value: Optional[float] = None,
            current_usage: Optional[float] = None,
            max_value: Optional[float] = None
    ):
        self.quota_type = quota_type
        self.user_id = user_id
        self.requested_value = requested_value
        self.current_usage = current_usage
        self.max_value = max_value

        message = f"Quota exceeded for {quota_type}"
        if user_id:
            message += f" (user: {user_id})"
        if requested_value is not None:
            message += f", requested: {requested_value}"
        if current_usage is not None and max_value is not None:
            message += f", current: {current_usage}, max: {max_value}"

        super().__init__(message)
