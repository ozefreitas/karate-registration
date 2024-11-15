from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Athlete(models.Model):
    GRADUATIONS = {
        "9": "9º Kyu",
        "8.5": "8º Kyu Karie",
        "8": "8º Kyu",
        "7.5": "7º Kyu Karie",
        "7": "7º Kyu",
        "6.5": "6º Kyu Karie",
        "6": "6º Kyu",
        "5.5": "5º Kyu Karie",
        "5": "5º Kyu",
        "4.5": "4º Kyu Karie",
        "4": "4º Kyu",
        "3.5": "3º Kyu Karie",
        "3": "3º Kyu",
        "2": "2º Kyu",
        "1": "1º Kyu",
        "1d": "1º Dan",
        "2d": "2º Dan",
        "3d": "3º Dan",
        "4d": "4º Dan",
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

    WEIGHTS = {
        'Juvenil': [
            ('-47', '-47Kg'),
            ('+47', '+47Kg'),
        ],
        'Cadete': [
            ('-57', '-57Kg'),
            ('+57', '+57Kg'),
        ],
        'Júnior': [
            ('-65', '-65Kg'),
            ('+65', '+65Kg'),
        ],
        'Sénior e Veterano': [
            ('-75', '-75Kg'),
            ('+75', '+75Kg'),
        ],
    }

    first_name = models.CharField("Primeiro Nome", max_length=200)
    last_name = models.CharField("Último Nome", max_length=200)
    graduation = models.CharField("Graduação", max_length=3, choices=GRADUATIONS)
    birth_date = models.DateField("Data de Nascimento")
    gender = models.CharField("Género", choices=GENDERS, max_length=10)
    skip_number = models.IntegerField("Nº SKI-P", blank=True, null=True)
    category = models.CharField("Escalão", choices=CATEGORIES, max_length=99)
    match_type = models.CharField("Prova", choices=MATCHES, max_length=10)
    weight = models.CharField("Peso", choices=WEIGHTS, max_length=10, blank=True, null=True)
    dojo = models.ForeignKey(User, on_delete=models.CASCADE)
    additional_emails = models.EmailField("Emails adicionais")

    def __str__(self): 
        return "{} {}".format(self.first_name, self.last_name)


class Dojo(models.Model):
    dojo = models.CharField("Dojo", max_length=99)