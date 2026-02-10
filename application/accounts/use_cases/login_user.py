"""Authenticate user by email/password and return tokens."""

from dataclasses import dataclass

from domain.accounts.entities import User
from domain.accounts.exceptions import InvalidCredentials, UserDisabled

from ..ports import TokenService, UserRepository


@dataclass
class LoginUserInput:
    email: str
    password: str


@dataclass
class LoginUserOutput:
    user: User
    access: str
    refresh: str


class LoginUser:
    def __init__(self, user_repo: UserRepository, token_service: TokenService) -> None:
        self._user_repo = user_repo
        self._token_service = token_service

    def execute(self, input: LoginUserInput) -> LoginUserOutput:
        email = input.email.strip().lower()
        user = self._user_repo.authenticate(email, input.password)
        if user is None:
            raise InvalidCredentials()
        if not user.is_active:
            raise UserDisabled()
        tokens = self._token_service.create_tokens_for_user(user)
        return LoginUserOutput(user=user, access=tokens.access, refresh=tokens.refresh)
