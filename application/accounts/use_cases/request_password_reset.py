"""Request a password reset email. Never leaks whether email exists."""

from dataclasses import dataclass
from typing import Callable

from ..ports import EmailSender, ResetTokenService, UserRepository


@dataclass
class RequestPasswordResetInput:
    email: str


class RequestPasswordReset:
    def __init__(
        self,
        user_repo: UserRepository,
        reset_token_service: ResetTokenService,
        email_sender: EmailSender,
    ) -> None:
        self._user_repo = user_repo
        self._reset_token_service = reset_token_service
        self._email_sender = email_sender

    def execute(self, input: RequestPasswordResetInput, reset_url_builder: Callable[[str], str]) -> None:
        email = input.email.strip().lower()
        user = self._user_repo.get_by_email(email)
        if user is not None and user.is_active:
            token = self._reset_token_service.generate(user.id)
            reset_url = reset_url_builder(token)
            self._email_sender.send_password_reset(email, reset_url)
