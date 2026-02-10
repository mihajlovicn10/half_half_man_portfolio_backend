"""Update current user profile (first_name, last_name)."""

from dataclasses import dataclass

from domain.accounts.entities import User

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
        return self._user_repo.update_profile(
            input.user_id,
            first_name=input.first_name,
            last_name=input.last_name,
        )
