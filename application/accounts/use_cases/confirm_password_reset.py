"""Confirm password reset with token and new password."""

from dataclasses import dataclass

from domain.accounts.exceptions import InvalidResetToken

from ..ports import ResetTokenService, UserRepository


@dataclass
class ConfirmPasswordResetInput:
    token: str
    new_password: str


class ConfirmPasswordReset:
    def __init__(
        self,
        user_repo: UserRepository,
        reset_token_service: ResetTokenService,
    ) -> None:
        self._user_repo = user_repo
        self._reset_token_service = reset_token_service

    def execute(self, input: ConfirmPasswordResetInput) -> None:
        user_id = self._reset_token_service.resolve_user_id(input.token)
        if user_id is None:
            raise InvalidResetToken()
        self._user_repo.update_password(user_id, input.new_password)
