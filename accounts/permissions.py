"""
Transport-layer RBAC: who can call the endpoint (RBAC_PLAN.md §3.1, §4.1).

§4.1 Auth matrix → permission used:
  Register              → AllowOnlyGuest (Guest ✓; User/Buyer/Client ✗)
  Login, Password reset → AllowAny (all ✓)
  Refresh, Logout       → default (token in body; User+ in practice)
  Me, Password change   → IsRoleAtLeast(Role.USER) (Guest ✗; User/Buyer/Client ✓)

Future: Buyer+ endpoints → IsRoleAtLeast(Role.BUYER); Client-only → IsRole(Role.CLIENT).
"""

from rest_framework.permissions import BasePermission

from domain.accounts.roles import Role


def get_request_role(request):
    """
    Resolve request.user to business role.
    Anonymous → Guest. Authenticated → Role from user.role (user/buyer/client).
    """
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return Role.GUEST
    role_value = getattr(request.user, "role", "user") or "user"
    try:
        return Role(role_value)
    except ValueError:
        return Role.USER


class IsRoleAtLeast(BasePermission):
    """
    Allow only if the request's role has at least the given privilege.
    E.g. IsRoleAtLeast(Role.USER) allows User, Buyer, Client.
    """

    def __init__(self, minimum: Role):
        self.minimum = minimum

    def has_permission(self, request, view):
        role = get_request_role(request)
        return role.satisfies_minimum(self.minimum)


class IsRole(BasePermission):
    """Allow only if the request's role equals the given role."""

    def __init__(self, role: Role):
        self.role = role

    def has_permission(self, request, view):
        return get_request_role(request) == self.role


# Concrete classes for permission_classes (DRF instantiates with ()); use these in views.
class IsRoleAtLeastUser(IsRoleAtLeast):
    def __init__(self):
        super().__init__(Role.USER)


class IsRoleAtLeastBuyer(IsRoleAtLeast):
    def __init__(self):
        super().__init__(Role.BUYER)


class IsClientOnly(IsRole):
    def __init__(self):
        super().__init__(Role.CLIENT)


class AllowOnlyGuest(BasePermission):
    """
    Allow only unauthenticated (Guest). Deny User/Buyer/Client.
    Use for Register so "already user" cannot call it (RBAC_PLAN §4.1).
    """

    def has_permission(self, request, view):
        return not (getattr(request, "user", None) and request.user.is_authenticated)
