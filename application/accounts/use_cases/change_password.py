"""Change password for an authenticated user."""

from dataclasses import dataclass

from domain.accounts.exceptions import InvalidCredentials
from domain.accounts.roles import Role

from ..authorization import require_role_at_least
from ..ports import UserRepository


@dataclass
class ChangePasswordInput:
    user_id: int
    old_password: str
    new_password: str


class ChangePassword:
    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    def execute(self, input: ChangePasswordInput) -> None:
        user = self._user_repo.get_by_id(input.user_id)
        if user is None:
            raise InvalidCredentials()
        require_role_at_least(user.role, Role.USER)
        authenticated = self._user_repo.authenticate(user.email, input.old_password)
        if authenticated is None:
            raise InvalidCredentials()
        self._user_repo.update_password(input.user_id, input.new_password)
