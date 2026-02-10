"""Port: password reset token (signed, time-limited). Implemented by infrastructure."""

from typing import Protocol


class ResetTokenService(Protocol):
    def generate(self, user_id: int) -> str: ...
    def resolve_user_id(self, token: str) -> int | None: ...
