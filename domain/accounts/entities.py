"""Domain entity: User. No Django or I/O."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=False)
class User:
    """User aggregate. id is None for not-yet-persisted."""
    id: Optional[int]
    email: str
    first_name: str
    last_name: str
    is_active: bool
    date_joined: datetime

    def __post_init__(self) -> None:
        self.email = self.email.lower().strip()
