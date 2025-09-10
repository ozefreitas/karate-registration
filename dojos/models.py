from django.db import models
from django.utils.text import slugify
from django.conf import settings
from datetime import timedelta
from django.utils import timezone

# Create your models here.

class Profile(models.Model):
    dojo = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    image = models.ImageField("Imagem de perfil", default='skip-logo.png', upload_to='profile_pictures')
    dojo_contact = models.IntegerField("Contacto do Dojo", default=123456789)
    cellphone_number = models.IntegerField("Número de telemóvel pessoal", default=123456789)

    def __str__(self):
        return f'{self.dojo.username} profile'


class Event(models.Model):
    SEASONS = {
        "2024/2025": "2024/2025",
        "2025/2026": "2025/2026",
        "2026/2027": "2026/2027",
        "2027/2028": "2027/2028",
        "2028/2029": "2028/2029",
        "2029/2030": "2029/2030",
        "2030/2031": "2030/2031",
        "2031/2032": "2031/2032",
        "2032/2033": "2032/2033",
        "2033/2034": "2033/2034",
        "2034/2035": "2034/2035",
        "2035/2036": "2035/2036",
        "2036/2037": "2036/2037",
        "2037/2038": "2037/2038",
        "2038/2039": "2038/2039",
        "2039/2040": "2039/2040",
    }

    ENCOUNTERS = {
        "none": "None",
        "regional": "Regional",
        "nacional": "Nacional",
        "internacional": "Internacional",
        "intrutores": "Instrutores",
        "formacao": "Formação",
        "exames": "Sessão de Exames",
        "seminario": "Seminário"
    }

    id = models.SlugField(primary_key=True, unique=True, max_length=100, blank=True)
    name = models.CharField("Nome", max_length=99)
    location = models.CharField("Local", max_length=99)
    season = models.CharField("Época", choices=SEASONS, max_length=15)
    start_registration = models.DateField("Início das inscrições", null=True, blank=True)
    end_registration = models.DateField("Fim das inscrições", null=True, blank=True)
    retifications_deadline = models.DateField("Fim do periodo de retificações", null=True, blank=True)
    event_date = models.DateField("Dia da prova")
    description = models.TextField("Descrição", default="", blank=True, null=True)
    custody = models.CharField("Tutela", max_length=99, default="", null=True, blank=True)
    email_contact = models.EmailField("Email", default="jpsfreitas19@gmail.com", null=True, blank=True)
    contact = models.PositiveIntegerField("Contacto", default="123456789", null=True, blank=True)
    individuals = models.ManyToManyField("registration.Athlete", related_name='general_events', blank=True)
    has_ended = models.BooleanField(default=False)
    has_registrations = models.BooleanField(default=False)
    has_categories = models.BooleanField(default=False)
    has_teams = models.BooleanField(default=False)
    encounter = models.BooleanField("É estágio/encontro", default=False)
    encounter_type = models.CharField("Estágio", choices=ENCOUNTERS, max_length=16, blank=True, null=True, default=ENCOUNTERS["none"])
    rating = models.IntegerField("Avaliação", default=0)

    def save(self, *args, **kwargs):
        if not self.id:  # Auto-generate slug only if not set
            self.id = slugify(f"{self.name} {self.season}")

        super().save(*args, **kwargs)

    def __str__(self):
        return '{} {}'.format(self.name, self.season)
    

class Discipline(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='disciplines')
    name = models.CharField("Nome", max_length=100)
    is_team = models.BooleanField(default=False)
    individuals = models.ManyToManyField("registration.Athlete", related_name='disciplines_indiv', blank=True)
    teams = models.ManyToManyField("registration.Team", related_name='disciplines_team', blank=True)
    categories = models.ManyToManyField("core.category", related_name='event_categories', blank=True)

    def __str__(self):
        return '{} {}'.format(self.event.name, self.name)


class DojosRatingAudit(models.Model):
    dojo = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, editable=False)
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

    class TYPE(models.TextChoices):
        NONE = "none", "None"
        REQ = "request", "Request"
        CREATE_ATHLETE = "create_athlete", "Create Athlete"
        RATE_EVENT = "rate_event", "Rate Event"

    urgency = models.CharField(max_length=10, choices=URGENCY_TYPE.choices, default=URGENCY_TYPE.NONE)
    type = models.CharField(max_length=16, choices=TYPE.choices, default=TYPE.NONE)
    request_acount = models.CharField(max_length=128, unique=True, null=True, blank=True)
    dojo = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    can_remove = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return self.created_at < timezone.now() - timedelta(days=30) 
    
    def __str__(self):
        return '{} {} notification'.format(self.dojo, self.urgency)