import secrets

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

JOIN_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_join_code():
    while True:
        code = "".join(secrets.choice(JOIN_CODE_ALPHABET) for _ in range(8))
        if not Business.objects.filter(join_code=code).exists():
            return code


class Business(models.Model):
    name = models.CharField(max_length=120)
    join_code = models.CharField(max_length=8, unique=True, default=generate_join_code, editable=False)
    timezone = models.CharField(max_length=64, default="UTC")
    max_hours_per_week = models.PositiveSmallIntegerField(
        default=40, validators=[MinValueValidator(1), MaxValueValidator(168)]
    )
    min_rest_hours = models.PositiveSmallIntegerField(
        default=10, validators=[MaxValueValidator(24)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        user = self.model(email=self.normalize_email(email).lower(), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.MANAGER)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        MANAGER = "manager"
        WORKER = "worker"

    username = None
    first_name = None
    last_name = None
    name = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.WORKER)
    business = models.ForeignKey(Business, null=True, blank=True, on_delete=models.PROTECT, related_name="members")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    objects = UserManager()

    def __str__(self):
        return self.email
