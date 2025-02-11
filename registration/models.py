from django.db import models
from django.contrib.auth.models import User
from dojos.models import CompetitionDetail

# Create your models here.

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


# Athletes models ###

class AthleteBase(models.Model):

    GENDERS = {
        "masculino": "Masculino",
        "feminino": "Feminino"
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

    first_name = models.CharField("Primeiro Nome", max_length=200)
    last_name = models.CharField("Último Nome", max_length=200)
    graduation = models.CharField("Graduação", max_length=4, choices=GRADUATIONS)
    birth_date = models.DateField("Data de Nascimento")
    age = models.IntegerField("Idade", default=25)
    skip_number = models.IntegerField("Nº SKI-P", blank=True, null=True)
    category = models.CharField("Escalão", choices=CATEGORIES, max_length=99)
    match_type = models.CharField("Prova", choices=MATCHES, max_length=10)
    gender = models.CharField("Género", choices=GENDERS, max_length=10)
    weight = models.CharField("Peso", choices=WEIGHTS, max_length=10, blank=True, null=True)
    dojo = models.ForeignKey(User, on_delete=models.CASCADE)
    creation_date = models.DateTimeField(auto_now_add=True)

    def __str__(self): 
        return "{} {}".format(self.first_name, self.last_name)
    
    class Meta:
        abstract = True


# declaration to be registered in admin panel
class Athlete(AthleteBase):
    pass


class ArchivedAthlete(AthleteBase):
    competition = models.ForeignKey(CompetitionDetail, on_delete=models.CASCADE)
    archived_date = models.DateTimeField(auto_now_add=True)


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


### Teams models ###

class Team(models.Model):

    GENDERS = {
        "masculino": "Masculino",
        "feminino": "Feminino",
        "misto": "Misto"
    }

    dojo = models.ForeignKey(User, on_delete=models.CASCADE)
    athlete1 = models.ForeignKey(Athlete, verbose_name="Atleta 1", related_name="first_element", on_delete=models.CASCADE)
    athlete2 = models.ForeignKey(Athlete, verbose_name="Atleta 2", related_name="second_element", on_delete=models.CASCADE)
    athlete3 = models.ForeignKey(Athlete, verbose_name="Atleta 3", related_name="third_element", on_delete=models.CASCADE, blank=True, null=True)
    athlete4 = models.ForeignKey(Athlete, verbose_name="Atleta 4", related_name="forth_element", on_delete=models.CASCADE, blank=True, null=True)
    athlete5 = models.ForeignKey(Athlete, verbose_name="Atleta 5", related_name="fifth_element", on_delete=models.CASCADE, blank=True, null=True)
    category = models.CharField("Escalão", choices=CATEGORIES, max_length=99)
    match_type = models.CharField("Prova", choices=MATCHES, max_length=10)
    gender = models.CharField("Género", choices=GENDERS, max_length=10)
    additional_emails = models.EmailField("Emails adicionais", blank=True, null=True)
    team_number = models.IntegerField("Nº Equipa")
    creation_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{} {} {}".format(self.match_type, self.category, self.gender)


class TeamFilter(models.Model):
    ORDER_BY = {
        "category": "Categoria",
        "gender": "Género",
        "match_type": "Prova"
    }

    order = models.CharField("Ordenar por", choices=ORDER_BY, max_length=20, blank=True, null=True)
    filter = models.CharField("Filtrar por", choices=ORDER_BY, max_length=20, blank=True, null=True)
    search = models.CharField("Procurar", max_length=99, blank=True, null=True)


### Coaches models ###

class CoachBase(models.Model):
    first_name = models.CharField("Primeiro Nome", max_length=200)
    last_name = models.CharField("Último Nome", max_length=200)
    graduation = models.CharField("Graduação", max_length=4, choices=GRADUATIONS)
    birth_date = models.DateField("Data de Nascimento")
    age = models.IntegerField("Idade", default=25)
    skip_number = models.IntegerField("Nº SKI-P", blank=True, null=True)
    # creation_date = models.DateTimeField(auto_now_add=True)

    def __str__(self): 
        return "{} {}".format(self.first_name, self.last_name)

    class Meta:
        abstract = True


# declaration to be registered in admin panel
class Coach(CoachBase):
    pass


class ArchivedCoach(CoachBase):
    competition = models.ForeignKey(CompetitionDetail, on_delete=models.CASCADE)
    archived_date = models.DateTimeField(auto_now_add=True)


### Dojos models ###

class Dojo(models.Model):
    dojo = models.CharField("Dojo", max_length=99, unique=True)
    is_registered = models.BooleanField(default=False)

    def __str__(self):
        return self.dojo