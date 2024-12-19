from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Profile(models.Model):
    dojo = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField("Imagem de perfil", default='skip-logo.png', upload_to='profile_pictures')
    dojo_contact = models.IntegerField("Contacto do Dojo", default=123456789)
    cellphone_number = models.IntegerField("Número de telemóvel pessoal", default=123456789)

    def __str__(self):
        return f'{self.dojo.username} profile'

class CompetitionsDetails(models.Model):
    name = models.CharField("Nome", max_length=99)
    start_registration = models.DateField("Início das inscrições")
    end_registration = models.DateField("Fim das inscrições")
    retifications_deadline = models.DateField("Fim do periodo de retificações")
    competition_date = models.DateField("Dia da prova")
    has_ended = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    
class FeedbackData(models.Model):
    first_name = models.CharField("Primeiro Nome", max_length=100)
    last_name = models.CharField("Último Nome", max_length=100)
    email = models.EmailField()
    feedback = models.TextField()

    def __str__(self):
        return '{} {}'.format(self.first_name, self.last_name)