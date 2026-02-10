"""EmailSender implementation using Django send_mail."""

from django.conf import settings
from django.core.mail import send_mail


class DjangoEmailSender:
    def send_password_reset(self, to_email: str, reset_url: str) -> None:
        send_mail(
            subject="Password reset",
            message=f"Use this link to reset your password: {reset_url}",
            from_email=settings.DEFAULT_FROM_EMAIL or "noreply@example.com",
            recipient_list=[to_email],
            fail_silently=True,
        )
