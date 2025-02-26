from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User

# Create your models here.

class Profile(models.Model):
    dojo = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField("Imagem de perfil", default='skip-logo.png', upload_to='profile_pictures')
    dojo_contact = models.IntegerField("Contacto do Dojo", default=123456789)
    cellphone_number = models.IntegerField("Número de telemóvel pessoal", default=123456789)

    def __str__(self):
        return f'{self.dojo.username} profile'


class CompetitionDetail(models.Model):
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

    id = models.SlugField(primary_key=True, unique=True, max_length=100, blank=True)
    name = models.CharField("Nome", max_length=99)
    location = models.CharField("Local", max_length=99)
    season = models.CharField("Época", choices=SEASONS, max_length=15)
    start_registration = models.DateField("Início das inscrições")
    end_registration = models.DateField("Fim das inscrições")
    retifications_deadline = models.DateField("Fim do periodo de retificações")
    competition_date = models.DateField("Dia da prova")
    has_ended = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.id:  # Auto-generate slug only if not set
            self.id = slugify(f"{self.name} {self.season}")
        super().save(*args, **kwargs)

    def __str__(self):
        return '{} {}'.format(self.name, self.season)


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