from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from .constants import GRADUATIONS, GENDERS
import uuid
from django.utils import timezone
from datetime import timedelta

# Create your models here.

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db.models import Q, UniqueConstraint


class User(AbstractUser):
    class Meta:
        app_label = "core"
        constraints = [
            # Ensure there can only ever be one MAINADMIN
            UniqueConstraint(
                fields=["role"],
                condition=Q(role="main_admin"),
                name="unique_main_admin",
            )
        ]

    class Role(models.TextChoices):
        SUPERUSER = "superuser", "Superuser"
        MAINADMIN = "main_admin", "Main Admin"
        SINGLEADMIN = "single_admin", "Single Admin"
        FREEDOJO = "free_dojo", "Dojo Free"
        SUBEDDOJO = "subed_dojo", "Dojo Subscription"

    class Tier(models.TextChoices):
        BASE = "base", "Base"
        PRO = "pro", "Pro"
        ELITE = "elite", "Elite"

    role = models.CharField(
        max_length=32,
        choices=Role.choices,
        default=Role.FREEDOJO,
    )

    tier = models.CharField(
        max_length=16,
        choices=Tier.choices,
        default=Tier.BASE,
    )

    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        limit_choices_to={"role": Role.MAINADMIN},  # only MAINADMIN can be a parent
    )

    # --------------------------
    # Validation rules
    # --------------------------
    def clean(self):
        # SUPERUSER restriction
        if self.role == self.Role.SUPERUSER and self.username != "ozefreitas":
            raise ValidationError("Only the user 'ozefreitas' can be Superuser.")

        # MAINADMIN restriction
        if self.role == self.Role.MAINADMIN and self.username != "SKIPortugal":
            raise ValidationError("Only the user 'SKIPortugal' can be Main Admin.")

        # SINGLEADMIN restrictions
        if self.role == self.Role.SINGLEADMIN:
            if self.children.exists():
                raise ValidationError("A Single Admin cannot have child accounts.")
            if self.parent is not None:
                raise ValidationError("A Single Admin cannot be assigned as a child.")

        # Child rules
        if self.parent and self.parent.role != self.Role.MAINADMIN:
            raise ValidationError("Child accounts must have a Main Admin as parent.")

        super().clean()

    # --------------------------
    # Persistence logic
    # --------------------------
    def save(self, *args, **kwargs):
        # Auto-assign SUPERUSER + tier
        if self.username == "ozefreitas":
            self.role = self.Role.SUPERUSER
            self.tier = self.Tier.ELITE

        # Auto-assign MAINADMIN
        elif self.username == "SKIPortugal":
            self.role = self.Role.MAINADMIN

        # Validate rules before saving
        self.full_clean()
        super().save(*args, **kwargs)



class RequestedAcount(models.Model):
    username = models.CharField(max_length=128, unique=True)
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    id_number = models.CharField(max_length=64)
    email = models.EmailField()

    def __str__(self): 
        return "Request for {} username".format(self.username)


class SignupToken(models.Model):
    username = models.CharField(max_length=128, unique=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    is_used = models.BooleanField(default=False)
    alive_time = models.SmallIntegerField(default=3)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return self.created_at < timezone.now() - timedelta(days=self.alive_time) 
    
    def __str__(self): 
        return "{} sign up token".format(self.username)
    

class RequestPasswordReset(models.Model):
    dojo_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reset_requests", editable=False)
    requested_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): 
        return "{} password reset request".format(self.dojo_user)


class Category(models.Model):
    name = models.CharField("Escalão", max_length=100)
    min_age = models.PositiveSmallIntegerField("Idade Mínima (inclusivé)", null=True, blank=True)
    max_age = models.PositiveSmallIntegerField("Idade Máxima (inclusivé)", null=True, blank=True)
    min_grad = models.CharField("Graduação Mínima (inclusivé)", max_length=4, choices=GRADUATIONS, null=True, blank=True)
    max_grad = models.CharField("Graduação Máxima (inclusivé)", max_length=4, choices=GRADUATIONS, null=True, blank=True)
    min_weight = models.PositiveSmallIntegerField("Peso Mínimo (inclusivé)", null=True, blank=True)
    max_weight = models.PositiveSmallIntegerField("Peso Máximo (inclusivé)", null=True, blank=True)
    gender = models.CharField("Género", choices=GENDERS, max_length=10)
    creation_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["min_age"]

    def __str__(self): 
        return "{} {}".format(self.name, self.gender)


class Ranking(models.Model):
    pass