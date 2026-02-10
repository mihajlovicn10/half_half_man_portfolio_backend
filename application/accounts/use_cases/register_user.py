"""Register a new user and return tokens."""

from dataclasses import dataclass

from domain.accounts.entities import User
from domain.accounts.exceptions import UserAlreadyExists

from ..ports import UserRepository, TokenService


@dataclass
class RegisterUserInput:
    email: str
    password: str
    first_name: str = ""
    last_name: str = ""


@dataclass
class RegisterUserOutput:
    user: User
    access: str
    refresh: str


class RegisterUser:
    def __init__(self, user_repo: UserRepository, token_service: TokenService) -> None:
        self._user_repo = user_repo
        self._token_service = token_service

    def execute(self, input: RegisterUserInput) -> RegisterUserOutput:
        email = input.email.strip().lower()
        if self._user_repo.exists_by_email(email):
            raise UserAlreadyExists()
        user = self._user_repo.create(
            email=email,
            password=input.password,
            first_name=input.first_name,
            last_name=input.last_name,
        )
        tokens = self._token_service.create_tokens_for_user(user)
        return RegisterUserOutput(user=user, access=tokens.access, refresh=tokens.refresh)
