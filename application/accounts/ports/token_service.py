"""Port: JWT token creation and blacklist. Implemented by infrastructure."""

from dataclasses import dataclass
from typing import Protocol

from domain.accounts.entities import User


@dataclass
class TokenPair:
    access: str
    refresh: str


class TokenService(Protocol):
    def create_tokens_for_user(self, user: User) -> TokenPair: ...
    def blacklist_refresh(self, refresh_token: str) -> None: ...
    def refresh_access(self, refresh_token: str) -> str | None: ...
