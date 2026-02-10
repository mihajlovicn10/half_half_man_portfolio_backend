"""Composition root: wire adapters and use cases. Single place for dependency construction."""

from application.accounts.use_cases import (
    ChangePassword,
    ConfirmPasswordReset,
    LoginUser,
    RegisterUser,
    RequestPasswordReset,
    UpdateProfile,
)
from application.accounts.ports import TokenService

from .adapters import (
    DjangoEmailSender,
    DjangoUserRepository,
    JWTTokenService,
    SigningResetTokenService,
)

_user_repo = DjangoUserRepository()
_token_service: TokenService = JWTTokenService()
_email_sender = DjangoEmailSender()
_reset_token_service = SigningResetTokenService()

register_user = RegisterUser(_user_repo, _token_service)
login_user = LoginUser(_user_repo, _token_service)
change_password = ChangePassword(_user_repo)
update_profile = UpdateProfile(_user_repo)
request_password_reset = RequestPasswordReset(_user_repo, _reset_token_service, _email_sender)
confirm_password_reset = ConfirmPasswordReset(_user_repo, _reset_token_service)
