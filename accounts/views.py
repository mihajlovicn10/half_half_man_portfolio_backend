"""Thin HTTP layer: parse request → call use case → map response."""

from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from domain.accounts.exceptions import (
    InsufficientRole,
    InvalidCredentials,
    InvalidResetToken,
    UserAlreadyExists,
    UserDisabled,
)
from .permissions import AllowOnlyGuest, IsRoleAtLeastUser

from .composition_root import (
    change_password,
    confirm_password_reset,
    login_user,
    register_user,
    request_password_reset,
    update_profile,
)
from .serializers import (
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserSerializer,
)


def _user_to_response(user):
    """Map domain User or Django user to API response dict."""
    from django.contrib.auth import get_user_model
    if getattr(user, "date_joined", None) is not None and hasattr(user.date_joined, "isoformat"):
        date_joined = user.date_joined.isoformat()
    else:
        date_joined = None
    return {
        "id": user.id,
        "email": user.email,
        "first_name": getattr(user, "first_name", "") or "",
        "last_name": getattr(user, "last_name", "") or "",
        "is_active": getattr(user, "is_active", True),
        "date_joined": date_joined,
        "role": getattr(user, "role", "user") or "user",
    }


class AuthRateThrottle(AnonRateThrottle):
    scope = "auth"


class RegisterView(generics.GenericAPIView):
    serializer_class = RegisterSerializer
    permission_classes = (AllowOnlyGuest,)  # Guest only; User/Buyer/Client ✗ (§4.1)
    throttle_classes = (AuthRateThrottle,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        from application.accounts.use_cases.register_user import RegisterUserInput
        try:
            result = register_user.execute(RegisterUserInput(
                email=data["email"],
                password=data["password"],
                first_name=data.get("first_name", ""),
                last_name=data.get("last_name", ""),
            ))
        except UserAlreadyExists:
            return Response({"email": ["A user with this email already exists."]}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {
                "user": _user_to_response(result.user),
                "access": result.access,
                "refresh": result.refresh,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    throttle_classes = (AuthRateThrottle,)

    def post(self, request):
        email = (request.data.get("email") or "").strip().lower()
        password = request.data.get("password")
        if not email or not password:
            return Response({"detail": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            from application.accounts.use_cases.login_user import LoginUserInput
            result = login_user.execute(LoginUserInput(email=email, password=password))
        except InvalidCredentials:
            return Response({"detail": "Invalid email or password."}, status=status.HTTP_401_UNAUTHORIZED)
        except UserDisabled:
            return Response({"detail": "User account is disabled."}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({
            "user": _user_to_response(result.user),
            "access": result.access,
            "refresh": result.refresh,
        })


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (IsRoleAtLeastUser,)

    def get_object(self):
        return self.request.user

    def get(self, request, *args, **kwargs):
        return Response(_user_to_response(request.user))

    def patch(self, request, *args, **kwargs):
        serializer = self.get_serializer(instance=request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        from application.accounts.use_cases.update_profile import UpdateProfileInput
        try:
            updated = update_profile.execute(UpdateProfileInput(
                user_id=request.user.id,
                first_name=serializer.validated_data.get("first_name"),
                last_name=serializer.validated_data.get("last_name"),
            ))
        except InsufficientRole:
            return Response({"detail": "You do not have permission to perform this action."}, status=status.HTTP_403_FORBIDDEN)
        if updated is None:
            return Response(_user_to_response(request.user))
        return Response(_user_to_response(updated))


class PasswordChangeView(generics.GenericAPIView):
    serializer_class = PasswordChangeSerializer
    permission_classes = (IsRoleAtLeastUser,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            from application.accounts.use_cases.change_password import ChangePasswordInput
            change_password.execute(ChangePasswordInput(user_id=request.user.id, old_password=data["old_password"], new_password=data["new_password"]))
        except InsufficientRole:
            return Response({"detail": "You do not have permission to perform this action."}, status=status.HTTP_403_FORBIDDEN)
        except InvalidCredentials:
            return Response({"old_password": ["Current password is incorrect."]}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "Password changed successfully."})


class PasswordResetRequestView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = (AllowAny,)
    throttle_classes = (AuthRateThrottle,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        def build_url(token):
            return request.build_absolute_uri(f"/api/auth/password/reset/confirm/?token={token}")
        from application.accounts.use_cases.request_password_reset import RequestPasswordResetInput
        request_password_reset.execute(RequestPasswordResetInput(email=email), reset_url_builder=build_url)
        return Response({"detail": "If an account exists with this email, you will receive a password reset link."})


class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = (AllowAny,)
    throttle_classes = (AuthRateThrottle,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            from application.accounts.use_cases.confirm_password_reset import ConfirmPasswordResetInput
            confirm_password_reset.execute(ConfirmPasswordResetInput(token=data["token"], new_password=data["new_password"]))
        except InvalidResetToken:
            return Response({"detail": "Invalid or expired reset token."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "Password has been reset. You can log in with your new password."})


