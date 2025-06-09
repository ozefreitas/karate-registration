from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

# Create your models here.

class User(AbstractUser):
    class Role(models.TextChoices):
        SUPERUSER = "superuser", "Superuser"
        NATIONAL = "national_association", "National Association"
        DOJO = "dojo", "Dojo"

    role = models.CharField(
        max_length=32,
        choices=Role.choices,
        default=Role.DOJO
    )

    def is_national(self):
        return self.role == self.Role.NATIONAL

    def is_dojo(self):
        return self.role == self.Role.DOJO
    
    def save(self, *args, **kwargs):
        if self.username == "ozefreitas":
            self.role = self.Role.SUPERUSER

        if self.username == "SKIPortugal":
            self.role = self.Role.NATIONAL
            existing = User.objects.filter(role=self.Role.NATIONAL).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError("There can only be one National Association account.")
        else:
            if self.role == self.Role.NATIONAL:
                raise ValidationError("Only the user with username 'SKIPortugal' can be National Association.")
        super().save(*args, **kwargs)
    

class Profile(models.Model):
    dojo = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField("Imagem de perfil", default='skip-logo.png', upload_to='profile_pictures')
    dojo_contact = models.IntegerField("Contacto do Dojo", default=123456789)
    cellphone_number = models.IntegerField("Número de telemóvel pessoal", default=123456789)

    def __str__(self):
        return f'{self.dojo.username} profile'


class Event(models.Model):
    SEASONS = {
        "2425": "2024/2025",
        "2526": "2025/2026",
        "2627": "2026/2027",
        "2728": "2027/2028",
        "2829": "2028/2029",
        "2930": "2029/2030",
        "3031": "2030/2031",
        "3132": "2031/2032",
        "3233": "2032/2033",
        "3334": "2033/2034",
        "3435": "2034/2035",
        "3536": "2035/2036",
        "3637": "2036/2037",
        "3738": "2037/2038",
        "3839": "2038/2039",
        "3940": "2039/2040",
    }

    ENCOUNTERS = {
        "none": "None",
        "regional": "Regional",
        "nacional": "Nacional",
        "internacional": "Internacional"
    }

    id = models.SlugField(primary_key=True, unique=True, max_length=100, blank=True)
    name = models.CharField("Nome", max_length=99)
    location = models.CharField("Local", max_length=99)
    season = models.CharField("Época", choices=SEASONS, max_length=15)
    start_registration = models.DateField("Início das inscrições")
    end_registration = models.DateField("Fim das inscrições")
    retifications_deadline = models.DateField("Fim do periodo de retificações")
    competition_date = models.DateField("Dia da prova")
    description = models.TextField("Descrição", default="", blank=True, null=True)
    custody = models.CharField("Tutela", max_length=99, default="")
    email_contact = models.EmailField("Email", default="jpsfreitas19@gmail.com")
    contact = models.PositiveIntegerField("Contacto", default="123456789")
    individuals = models.ManyToManyField("registration.Athlete", related_name='events', blank=True)
    teams = models.ManyToManyField("registration.Team", related_name='events', blank=True)
    has_ended = models.BooleanField(default=False)
    has_teams = models.BooleanField(default=False)
    encounter = models.BooleanField("É estágio/encontro", default=False)
    encounter_type = models.CharField("Estágio", choices=ENCOUNTERS, max_length=16, blank=True, null=True, default=ENCOUNTERS["none"])
    rating = models.IntegerField("Avaliação", default=0)

    def save(self, *args, **kwargs):
        if not self.id:  # Auto-generate slug only if not set
            self.id = slugify(f"{self.name} {self.season}")
        super().save(*args, **kwargs)

        if "torneio" in self.name.lower():
            self.has_teams = True

    def __str__(self):
        return '{} {}'.format(self.name, self.season)


class DojosRatingAudit(models.Model):
    dojo = models.ForeignKey(User, on_delete=models.CASCADE, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, editable=False)
    rating = models.IntegerField("Avaliação", default=0, editable=False)

    def __str__(self):
        return '{} {} rating'.format(self.dojo, self.event)


class FeedbackData(models.Model):
    first_name = models.CharField("Primeiro Nome", max_length=100)
    last_name = models.CharField("Último Nome", max_length=100)
    email = models.EmailField()
    feedback = models.TextField()

    def __str__(self):
        return '{} {}'.format(self.first_name, self.last_name)


class PasswordConfirmReset(models.Model):
    new_password1 = models.CharField("Palavra Passe", max_length=36)
    new_password2 = models.CharField("Repetir Palavra Passe", max_length=36)


class Announcement(models.Model):
    message = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Notification(models.Model):
    notification = models.TextField()

    class URGENCY_TYPE(models.TextChoices):
        NONE = "none", "None"
        GREEN = "green", "Green"
        YELLOW = "yellow", "Yellow"
        ORANGE = "orange", "Orange"
        RED = "red", "Red"
        BLACK = "black", "Black"

    urgency = models.CharField(max_length=10, choices=URGENCY_TYPE.choices, default=URGENCY_TYPE.NONE)
    dojo = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)