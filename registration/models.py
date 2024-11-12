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

    GENDERS = {
        "male": "Masculino",
        "female": "Feminino"
    }

    CATEGORIES = {
        "infantil": "Infantil",
        "iniciado": "Iniciado",
        "juvenil": "Juvenil",
        "cadete": "Cadete",
        "junior": "Júnior",
        "senior": "Sénior",
        "veterano": "Veterano"
    }

    MATCHES = {
        "kata": "Kata",
        "kumite": "Kumite"
    }

    first_name = models.CharField("Primeiro Nome", max_length=200)
    last_name = models.CharField("Último Nome", max_length=200)
    graduation = models.CharField("Graduação", max_length=1, choices=GRADUATIONS, blank=True)
    birth_date = models.DateField("Data de Nascimento")
    gender = models.CharField("Género", choices=GENDERS, max_length=10)
    skip_number = models.IntegerField("Nº SKI-P", blank=True)
    category = models.CharField("Escalão", choices=CATEGORIES, max_length=99)
    match_type = models.CharField("Prova", choices=MATCHES, max_length=10, required=False)


class Dojo(models.Model):
    dojo = models.CharField("Dojo", max_length=99)