from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from .constants import GRADUATIONS, GENDERS
import uuid
from django.utils import timezone
from datetime import timedelta

# Create your models here.

class User(AbstractUser):

    class Meta:
        app_label = 'core'

    class Role(models.TextChoices):
        SUPERUSER = "superuser", "Superuser"
        MAINADMIN = "main_admin", "Main Admin"
        FREEDOJO = "free_dojo", "Dojo Free"
        SUBEDDOJO = "subed_dojo", "Dojo Subscription"

    class Tier(models.TextChoices):
        BASE = "base", "Base"
        PRO = "pro", "Pro"
        ELITE = "elite", "Elite"

    role = models.CharField(
        max_length=32,
        choices=Role.choices,
        default=Role.FREEDOJO
    )

    tier = models.CharField(
        max_length=16,
        choices=Tier.choices,
        default=Tier.BASE
    )

    def is_main_admin(self):
        return self.role == self.Role.MAINADMIN

    def is_free_dojo(self):
        return self.role == self.Role.FREEDOJO
    
    def is_subed_dojo(self):
        return self.role == self.Role.SUBEDDOJO
    
    def save(self, *args, **kwargs):
        if self.username == "ozefreitas":
            self.role = self.Role.SUPERUSER
            self.tier = self.Tier.ELITE
        
        else:
            if self.role == self.Role.SUPERUSER:
                raise ValidationError("Only Freitas can be the superuser.")

        if self.username == "SKIPortugal":
            self.role = self.Role.MAINADMIN
            existing = User.objects.filter(role=self.Role.MAINADMIN).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError("There can only be one Main Admin account.")
        else:
            if self.role == self.Role.MAINADMIN:
                raise ValidationError("Only the user with username 'SKIPortugal' can be Main Admin.")
            
        super().save(*args, **kwargs)


class SignupToken(models.Model):
    username = models.CharField(max_length=150, unique=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    is_used = models.BooleanField(default=False)
    alive_time = models.SmallIntegerField(default=3)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return self.created_at < timezone.now() - timedelta(days=self.alive_time) 
    
    def __str__(self): 
        return "{} sign up token".format(self.username)


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

    def __str__(self): 
        return "{} {}".format(self.name, self.gender)


class Ranking(models.Model):
    pass