"""Domain and application exceptions. No framework dependencies."""


class UserAlreadyExists(Exception):
    """A user with this email already exists."""


class InvalidCredentials(Exception):
    """Email or password is invalid."""


class UserDisabled(Exception):
    """User account is disabled."""


class InvalidResetToken(Exception):
    """Password reset token is invalid or expired."""
