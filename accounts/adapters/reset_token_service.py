"""ResetTokenService implementation using Django signing."""

from django.core import signing

RESET_SALT = "password-reset"
RESET_MAX_AGE = 60 * 60 * 24  # 24 hours


class SigningResetTokenService:
    def generate(self, user_id: int) -> str:
        return signing.TimestampSigner(salt=RESET_SALT).sign(user_id)

    def resolve_user_id(self, token: str) -> int | None:
        try:
            value = signing.TimestampSigner(salt=RESET_SALT).unsign(token, max_age=RESET_MAX_AGE)
            return int(value)
        except (signing.BadSignature, signing.SignatureExpired, ValueError, TypeError):
            return None
