"""
Business roles for RBAC (see docs/RBAC_PLAN.md §2).

Hierarchy: Guest < User < Buyer < Client.
Higher roles imply lower capabilities unless an action is restricted to a specific role.
Guest is never stored; USER, BUYER, CLIENT are persisted on User.
"""

from enum import Enum


class Role(str, Enum):
    """
    Business role of an actor.

    Guest: Unauthenticated or anonymous. Can browse public content, register,
        login, use password reset. Typical state: no user record.
    User: Registered and authenticated. Can manage own profile, change password,
        access protected content. Typical state: has account, role=USER.
    Buyer: Has made at least one purchase (or explicitly promoted). Can request
        refunds, see order history, buyer-only features. Typical state: role=BUYER.
    Client: Business relationship (e.g. ongoing work, retainer). May have
        different refund/contract rights than Buyer. Typical state: role=CLIENT.
    """

    GUEST = "guest"
    USER = "user"
    BUYER = "buyer"
    CLIENT = "client"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def at_least(cls, minimum: "Role") -> tuple["Role", ...]:
        """Roles with at least the given privilege (minimum and above)."""
        order = (cls.GUEST, cls.USER, cls.BUYER, cls.CLIENT)
        try:
            idx = order.index(minimum)
            return order[idx:]
        except ValueError:
            return ()

    def satisfies_minimum(self, minimum: "Role") -> bool:
        """True if this role has at least the privilege of minimum."""
        order = (Role.GUEST, Role.USER, Role.BUYER, Role.CLIENT)
        return order.index(self) >= order.index(minimum)
