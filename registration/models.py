from django.db import models
from django.contrib.auth.models import User
from dojos.models import CompetitionDetail
from django.apps import apps
from django.conf import settings
from nanoid import generate

# Create your models here.

CATEGORIES = {
    "Benjamins (n/SKIP)": "Benjamins (n/SKIP)",
    "Infantil": "Infantil",
    "Infantil A (7 8 9) (n/SKIP)": "Infantil A (7 8 9) (n/SKIP)",
    "Infantil B (7 8 9) (n/SKIP)": "Infantil B (7 8 9) (n/SKIP)",
    "Iniciado": "Iniciado",
    "Iniciado A 10 11 12 (n/SKIP)": "Iniciado A 10 11 12 (n/SKIP)",
    "Iniciado B 10 11 12 (n/SKIP)": "Iniciado B 10 11 12 (n/SKIP)",
    "Juvenil": "Juvenil",
    "Cadete": "Cadete",
    "Cadete 13 14 15 (n/SKIP)": "Cadete 13 14 15 (n/SKIP)",
    "Júnior": "Júnior",
    "Júnior 16 17 18 (n/SKIP)": "Júnior 16 17 18 (n/SKIP)",
    "Sénior": "Sénior",
    "Sénior 19+ (n/SKIP)": "Sénior 19+ (n/SKIP)",
    "Veterano +35": "Veterano +35",
    "Veterano +35 (n/SKIP)": "Veterano +35 (n/SKIP)",
    "Veterano +50": "Veterano +50",
}

MATCHES = {
        "kata": "Kata",
        "kumite": "Kumite"
}

def generate_unique_nanoid(model_name, app_label, size=10):
    """
    Generates a unique NanoID for a given model.
    Uses `apps.get_model()` to avoid import issues.
    """
    model = apps.get_model(app_label, model_name)  # Dynamically get model
    while True:
        new_id = generate(size=size)  # Generate NanoID
        if not model.objects.filter(id=new_id).exists():
            return new_id


### Athlete model ###

class Athlete(models.Model):
    GRADUATIONS = {
        "15": "9º Kyu",
        "14.5": "8º Kyu Kari",
        "14": "8º Kyu",
        "13.5": "7º Kyu Kari",
        "13": "7º Kyu",
        "12.5": "6º Kyu Kari",
        "12": "6º Kyu",
        "11.5": "5º Kyu Kari",
        "11": "5º Kyu",
        "10.5": "4º Kyu Kari",
        "10": "4º Kyu",
        "9.5": "3º Kyu Kari",
        "9": "3º Kyu",
        "8": "2º Kyu",
        "7": "1º Kyu",
        "6": "1º Dan",
        "5": "2º Dan",
        "4": "3º Dan",
        "3": "4º Dan",
        "2": "5º Dan",
        "1": "6º Dan",
    }

    GENDERS = {
        "masculino": "Masculino",
        "feminino": "Feminino",
        "misto": "Misto"
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
            ('open', 'Open'),
        ],
    }

    id = models.CharField(primary_key=True, max_length=10, unique=True, editable=False)
    first_name = models.CharField("Primeiro Nome", max_length=200)
    last_name = models.CharField("Último Nome", max_length=200)
    graduation = models.CharField("Graduação", max_length=4, choices=GRADUATIONS)
    birth_date = models.DateField("Data de Nascimento")
    age = models.IntegerField("Idade", default=25)
    skip_number = models.IntegerField("Nº SKI-P", blank=True, null=True)
    is_just_student = models.BooleanField("Aluno", default=False)
    category = models.CharField("Escalão", choices=CATEGORIES, max_length=99, blank=True, null=True)
    match_type = models.CharField("Prova", choices=MATCHES, max_length=10, blank=True, null=True)
    gender = models.CharField("Género", choices=GENDERS, max_length=10, blank=True, null=True)
    weight = models.CharField("Peso", choices=WEIGHTS, max_length=10, blank=True, null=True)
    dojo = models.ForeignKey(User, on_delete=models.CASCADE)
    creation_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.id:  # Generate only if no ID exists
            self.id = generate_unique_nanoid(self.__class__.__name__, self._meta.app_label)
            
        super().save(*args, **kwargs)

    def __str__(self):
        return "{} {} {}".format(self.first_name, self.last_name, self.dojo.username)


### Individual models ###

class Individual(models.Model):
    id = models.CharField(primary_key=True, max_length=10, unique=True, editable=False)
    dojo = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    athlete = models.ForeignKey(Athlete, on_delete=models.CASCADE)
    competition = models.ForeignKey(CompetitionDetail, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if not self.id:  # Generate only if no ID exists
            self.id = generate_unique_nanoid("Individual", "registration")
        super().save(*args, **kwargs)

    def __str__(self):
        return "{} {}".format(self.athlete.first_name, self.athlete.last_name)


### Dojo model ###

class Dojo(models.Model):
    dojo = models.CharField("Dojo", max_length=99, unique=True)
    is_registered = models.BooleanField(default=False)

    def __str__(self):
        return self.dojo


### Teams models ###

class Team(models.Model):

    GENDERS = {
        "masculino": "Masculino",
        "feminino": "Feminino",
        "misto": "Misto"
    }

    id = models.CharField(primary_key=True, max_length=10, unique=True, editable=False)
    dojo = models.ForeignKey(User, on_delete=models.CASCADE)
    athlete1 = models.ForeignKey(Athlete, verbose_name="Atleta 1", related_name="first_element", on_delete=models.CASCADE)
    athlete2 = models.ForeignKey(Athlete, verbose_name="Atleta 2", related_name="second_element", on_delete=models.CASCADE)
    athlete3 = models.ForeignKey(Athlete, verbose_name="Atleta 3", related_name="third_element", on_delete=models.CASCADE, blank=True, null=True)
    athlete4 = models.ForeignKey(Athlete, verbose_name="Atleta 4", related_name="forth_element", on_delete=models.CASCADE, blank=True, null=True)
    athlete5 = models.ForeignKey(Athlete, verbose_name="Atleta 5", related_name="fifth_element", on_delete=models.CASCADE, blank=True, null=True)
    category = models.CharField("Escalão", choices=CATEGORIES, max_length=99)
    match_type = models.CharField("Prova", choices=MATCHES, max_length=10)
    gender = models.CharField("Género", choices=GENDERS, max_length=10)
    team_number = models.IntegerField("Nº Equipa")
    competition = models.ForeignKey(CompetitionDetail, on_delete=models.CASCADE)
    creation_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.id:  # Generate only if no ID exists
            self.id = generate_unique_nanoid("Team", "registration")
        super().save(*args, **kwargs)

    def __str__(self):
        return "{} {} {}".format(self.match_type, self.category, self.gender)


### Filter models ###

class AthleteFilter(models.Model):
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


class TeamFilter(models.Model):
    ORDER_BY = {
        "category": "Categoria",
        "gender": "Género",
        "match_type": "Prova"
    }

    order = models.CharField("Ordenar por", choices=ORDER_BY, max_length=20, blank=True, null=True)
    filter = models.CharField("Filtrar por", choices=ORDER_BY, max_length=20, blank=True, null=True)
    search = models.CharField("Procurar", max_length=99, blank=True, null=True)