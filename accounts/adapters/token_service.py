"""TokenService implementation using simplejwt."""

from rest_framework_simplejwt.tokens import RefreshToken

from application.accounts.ports.token_service import TokenPair
from domain.accounts.entities import User


class JWTTokenService:
    def create_tokens_for_user(self, user: User) -> TokenPair:
        # We need a Django user for RefreshToken.for_user; get it by id
        from django.contrib.auth import get_user_model
        UserModel = get_user_model()
        django_user = UserModel.objects.get(pk=user.id)
        refresh = RefreshToken.for_user(django_user)
        return TokenPair(access=str(refresh.access_token), refresh=str(refresh))

    def blacklist_refresh(self, refresh_token: str) -> None:
        token = RefreshToken(refresh_token)
        token.blacklist()

    def refresh_access(self, refresh_token: str) -> str | None:
        try:
            refresh = RefreshToken(refresh_token)
            return str(refresh.access_token)
        except Exception:
            return None
