"""Port: send emails. Implemented by infrastructure."""

from typing import Protocol


class EmailSender(Protocol):
    def send_password_reset(self, to_email: str, reset_url: str) -> None: ...
