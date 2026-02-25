from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from . import views
from .adapters.reset_token_service import SigningResetTokenService

User = get_user_model()


def _disable_auth_throttle():
    """Disable throttling on auth views so tests can hit them repeatedly."""
    for attr in ("RegisterView", "LoginView", "PasswordResetRequestView", "PasswordResetConfirmView"):
        view_class = getattr(views, attr, None)
        if view_class is not None:
            view_class.throttle_classes = ()


class RegisterTests(TestCase):
    def setUp(self):
        _disable_auth_throttle()
        self.client = APIClient()
        self.url = reverse("register")

    def test_register_success(self):
        data = {
            "email": "user@example.com",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("user", response.data)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["email"], "user@example.com")
        self.assertTrue(User.objects.filter(email="user@example.com").exists())

    def test_register_with_names(self):
        data = {
            "email": "named@example.com",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
            "first_name": "First",
            "last_name": "Last",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user"]["first_name"], "First")
        self.assertEqual(response.data["user"]["last_name"], "Last")

    def test_register_duplicate_email(self):
        User.objects.create_user(email="existing@example.com", username="existing@example.com", password="old")
        data = {
            "email": "existing@example.com",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_register_password_mismatch(self):
        data = {
            "email": "user@example.com",
            "password": "SecurePass123!",
            "password_confirm": "DifferentPass123!",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password_confirm", response.data)

    def test_register_weak_password(self):
        data = {
            "email": "user@example.com",
            "password": "short",
            "password_confirm": "short",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_register_email_normalized(self):
        data = {
            "email": "User@EXAMPLE.com",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user"]["email"], "user@example.com")


class LoginTests(TestCase):
    def setUp(self):
        _disable_auth_throttle()
        self.client = APIClient()
        self.url = reverse("login")
        self.user = User.objects.create_user(
            email="login@example.com",
            username="login@example.com",
            password="GoodPass123!",
        )

    def test_login_success(self):
        data = {"email": "login@example.com", "password": "GoodPass123!"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["email"], "login@example.com")

    def test_login_wrong_password(self):
        data = {"email": "login@example.com", "password": "WrongPass123!"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

    def test_login_nonexistent_email(self):
        data = {"email": "nonexistent@example.com", "password": "GoodPass123!"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_inactive_user(self):
        self.user.is_active = False
        self.user.save()
        data = {"email": "login@example.com", "password": "GoodPass123!"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_missing_credentials(self):
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TokenRefreshTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("token_refresh")
        self.user = User.objects.create_user(
            email="refresh@example.com",
            username="refresh@example.com",
            password="pass",
        )

    def test_refresh_success(self):
        refresh = RefreshToken.for_user(self.user)
        response = self.client.post(
            self.url,
            {"refresh": str(refresh)},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_refresh_invalid_token(self):
        response = self.client.post(
            self.url,
            {"refresh": "invalid-token"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class LogoutTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("logout")
        self.user = User.objects.create_user(
            email="logout@example.com",
            username="logout@example.com",
            password="pass",
        )

    def test_logout_success(self):
        refresh = RefreshToken.for_user(self.user)
        response = self.client.post(
            self.url,
            {"refresh": str(refresh)},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Blacklisted token cannot be used to refresh
        refresh_url = reverse("token_refresh")
        response2 = self.client.post(refresh_url, {"refresh": str(refresh)}, format="json")
        self.assertEqual(response2.status_code, status.HTTP_401_UNAUTHORIZED)


class MeTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("me")
        self.user = User.objects.create_user(
            email="me@example.com",
            username="me@example.com",
            password="pass",
        )

    def test_me_unauthorized(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_get_success(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "me@example.com")

    def test_me_patch_success(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        response = self.client.patch(
            self.url,
            {"first_name": "Updated", "last_name": "Name"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"], "Updated")
        self.assertEqual(response.data["last_name"], "Name")
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")


class PasswordChangeTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("password_change")
        self.user = User.objects.create_user(
            email="pwd@example.com",
            username="pwd@example.com",
            password="OldPass123!",
        )

    def test_password_change_unauthorized(self):
        response = self.client.post(
            self.url,
            {"old_password": "OldPass123!", "new_password": "NewPass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_password_change_success(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        response = self.client.post(
            self.url,
            {"old_password": "OldPass123!", "new_password": "NewPass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPass123!"))

    def test_password_change_wrong_old_password(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        response = self.client.post(
            self.url,
            {"old_password": "WrongOld!", "new_password": "NewPass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("old_password", response.data)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class PasswordResetRequestTests(TestCase):
    def setUp(self):
        _disable_auth_throttle()
        self.client = APIClient()
        self.url = reverse("password_reset_request")
        self.user = User.objects.create_user(
            email="reset@example.com",
            username="reset@example.com",
            password="pass",
        )

    def test_reset_request_always_200(self):
        # Should not leak whether email exists
        response = self.client.post(
            self.url,
            {"email": "nonexistent@example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)

    def test_reset_request_sends_email_for_existing_user(self):
        from django.core.mail import outbox

        outbox.clear()
        response = self.client.post(
            self.url,
            {"email": "reset@example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(outbox), 1)
        self.assertEqual(outbox[0].to, ["reset@example.com"])
        self.assertIn("reset", outbox[0].body.lower())


class PasswordResetConfirmTests(TestCase):
    def setUp(self):
        _disable_auth_throttle()
        self.client = APIClient()
        self.url = reverse("password_reset_confirm")
        self.user = User.objects.create_user(
            email="confirm@example.com",
            username="confirm@example.com",
            password="OldPass123!",
        )

    def test_reset_confirm_success(self):
        token = SigningResetTokenService().generate(self.user.id)
        response = self.client.post(
            self.url,
            {"token": token, "new_password": "NewSecure123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewSecure123!"))

    def test_reset_confirm_invalid_token(self):
        response = self.client.post(
            self.url,
            {"token": "invalid-token", "new_password": "NewSecure123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)

    def test_reset_confirm_weak_password(self):
        token = SigningResetTokenService().generate(self.user.id)
        response = self.client.post(
            self.url,
            {"token": token, "new_password": "short"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("new_password", response.data)
