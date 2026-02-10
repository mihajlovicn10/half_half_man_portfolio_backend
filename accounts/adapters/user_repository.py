"""UserRepository implementation using Django ORM."""

from django.contrib.auth import get_user_model

from domain.accounts.entities import User

UserModel = get_user_model()


def _to_entity(m: UserModel) -> User:
    return User(
        id=m.id,
        email=m.email,
        first_name=m.first_name or "",
        last_name=m.last_name or "",
        is_active=m.is_active,
        date_joined=m.date_joined,
    )


class DjangoUserRepository:
    def get_by_id(self, user_id: int) -> User | None:
        try:
            m = UserModel.objects.get(pk=user_id)
            return _to_entity(m)
        except UserModel.DoesNotExist:
            return None

    def get_by_email(self, email: str) -> User | None:
        m = UserModel.objects.filter(email=email.strip().lower()).first()
        return _to_entity(m) if m else None

    def create(
        self,
        email: str,
        password: str,
        first_name: str = "",
        last_name: str = "",
    ) -> User:
        m = UserModel.objects.create_user(
            email=email.strip().lower(),
            username=email.strip().lower(),
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        return _to_entity(m)

    def update_profile(
        self,
        user_id: int,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> User | None:
        kwargs = {}
        if first_name is not None:
            kwargs["first_name"] = first_name
        if last_name is not None:
            kwargs["last_name"] = last_name
        if not kwargs:
            return self.get_by_id(user_id)
        updated = UserModel.objects.filter(pk=user_id).update(**kwargs)
        if not updated:
            return None
        return self.get_by_id(user_id)

    def update_password(self, user_id: int, new_password: str) -> None:
        m = UserModel.objects.get(pk=user_id)
        m.set_password(new_password)
        m.save(update_fields=["password"])

    def authenticate(self, email: str, password: str) -> User | None:
        m = UserModel.objects.filter(email=email.strip().lower()).first()
        if m is None or not m.check_password(password):
            return None
        return _to_entity(m)

    def exists_by_email(self, email: str) -> bool:
        return UserModel.objects.filter(email=email.strip().lower()).exists()
