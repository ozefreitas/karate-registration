from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Athlete(models.Model):
    GRADUATIONS = {
        "15": "9º Kyu",
        "14.5": "8º Kyu Karie",
        "14": "8º Kyu",
        "13.5": "7º Kyu Karie",
        "13": "7º Kyu",
        "12.5": "6º Kyu Karie",
        "12": "6º Kyu",
        "11.5": "5º Kyu Karie",
        "11": "5º Kyu",
        "10.5": "4º Kyu Karie",
        "10": "4º Kyu",
        "9.5": "3º Kyu Karie",
        "9": "3º Kyu",
        "8": "2º Kyu",
        "7": "1º Kyu",
        "6": "1º Dan",
        "5": "2º Dan",
        "4": "3º Dan",
        "3": "5º Dan",
        "2": "6º Dan",
        "1": "7º Dan",
    }

    GENDERS = {
        "masculino": "Masculino",
        "feminino": "Feminino"
    }

    CATEGORIES = {
        "Infantil": "Infantil",
        "Iniciado": "Iniciado",
        "Juvenil": "Juvenil",
        "Cadete": "Cadete",
        "Júnior": "Júnior",
        "Sénior": "Sénior",
        "Veterano +35": "Veterano +35",
        "Veterano +50": "Veterano +50"
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
    graduation = models.CharField("Graduação", max_length=4, choices=GRADUATIONS)
    birth_date = models.DateField("Data de Nascimento")
    age = models.IntegerField("Idade")
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
    dojo = models.CharField("Dojo", max_length=99, unique=True)
    is_registered = models.BooleanField(default=False)

    def __str__(self):
        return self.dojo
    
class Filters(models.Model):
    ORDER_BY = {
        "first_name": "Primeiro Nome",
        "last_name": "Último Nome",
        "birth_date": "Idade",
        "category": "Categoria",
        "gender": "Género",
        "match_type": "Prova"
    }

    order = models.CharField("Ordenar por", choices=ORDER_BY, max_length=20, blank=True, null=True)
    filter = models.CharField("Filtrar por", choices=ORDER_BY, max_length=20, blank=True, null=True)
    search = models.CharField("Procurar", max_length=99, blank=True, null=True)