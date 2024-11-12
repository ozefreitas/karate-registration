from django.db import models

# Create your models here.

class Athlete(models.Model):
    GRADUATIONS = {
        "9": "9º Kyu",
        "8": "8º Kyu",
        "7": "7º Kyu",
        "6": "6º Kyu",
        "5": "5º Kyu",
        "4": "4º Kyu",
        "3": "3º Kyu",
        "2": "2º Kyu",
        "1": "1º Kyu",
        
    }
    first_name = models.CharField(name="Primeiro Nome", max_length=200)
    last_name = models.CharField(name="Último Nome", max_length=200)
    graduation = models.CharField(name="Graduação", max_length=1, choices=GRADUATIONS, blank=True)
    