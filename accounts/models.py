from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user with email as the primary identifier (login).
    Username is kept for compatibility but derived from email if not provided.
    Role is a business concept for RBAC (User < Buyer < Client). Guest = unauthenticated.
    """
    class Role(models.TextChoices):
        USER = "user", "User"
        BUYER = "buyer", "Buyer"
        CLIENT = "client", "Client"

    email = models.EmailField("email address", unique=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.USER,
        db_index=True,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]  # used by createsuperuser; username still required by AbstractUser

    class Meta:
        db_table = "accounts_user"
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self):
        return self.email
