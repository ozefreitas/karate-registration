from django.db import models

# Create your models here.

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