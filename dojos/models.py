from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Profile(models.Model):
    dojo = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField("Imagem de perfil", default='skip-logo.png', upload_to='profile_pictures')

    def __str__(self):
        return f'{self.dojo.username} profile'

class CompetitionsDetails(models.Model):
    name = models.CharField("Nome", max_length=99)
    start_registration = models.DateField("Início das inscrições")
    end_registration = models.DateField("Fim das inscrições")
    competition_date = models.DateField("Dia da prova")

    def __str__(self):
        return self.name
    
class FeedbackData(models.Model):
    first_name = models.CharField("Primeiro Nome", max_length=100)
    last_name = models.CharField("Último Nome", max_length=100)
    email = models.EmailField()
    feedback = models.TextField()

    def __str__(self):
        return '{} {}'.format(self.first_name, self.last_name)