"""
Application-layer RBAC: who can execute the use case / action (RBAC_PLAN.md §3.2).
Use cases call require_role_at_least(caller_role, minimum) before doing work.
Raises domain exception if not allowed; this is the authoritative place for role checks.
"""

from domain.accounts.exceptions import InsufficientRole
from domain.accounts.roles import Role


def require_role_at_least(caller_role: Role, minimum: Role) -> None:
    """
    Raise InsufficientRole if caller_role does not have at least the given privilege.
    Call at the start of a use case that requires a minimum role.
    """
    if not caller_role.satisfies_minimum(minimum):
        raise InsufficientRole()
