"""Update current user profile (first_name, last_name)."""

from dataclasses import dataclass

from domain.accounts.entities import User
from domain.accounts.roles import Role

from ..authorization import require_role_at_least
from ..ports import UserRepository


@dataclass
class UpdateProfileInput:
    user_id: int
    first_name: str | None = None
    last_name: str | None = None


class UpdateProfile:
    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    def execute(self, input: UpdateProfileInput) -> User | None:
        user = self._user_repo.get_by_id(input.user_id)
        if user is None:
            return None
        require_role_at_least(user.role, Role.USER)
        return self._user_repo.update_profile(
            input.user_id,
            first_name=input.first_name,
            last_name=input.last_name,
        )
