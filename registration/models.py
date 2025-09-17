from django.db import models
from django.contrib.auth.models import User
from dojos.models import Event
from django.apps import apps
from django.utils import timezone
from nanoid import generate
from django.conf import settings
from django.core.exceptions import ValidationError
from core.constants import GENDERS, GRADUATIONS, MATCHES

# Create your models here.

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
    id = models.CharField(primary_key=True, max_length=10, unique=True, editable=False)
    first_name = models.CharField("Primeiro Nome", max_length=200)
    last_name = models.CharField("Último Nome", max_length=200)
    graduation = models.CharField("Graduação", max_length=4, choices=GRADUATIONS)
    birth_date = models.DateField("Data de Nascimento")
    id_number = models.PositiveIntegerField("Nº SKI-P", blank=True, null=True)
    competitor = models.BooleanField("Competidor", default=False)
    favorite = models.BooleanField("Favorito", default=False)
    gender = models.CharField("Género", choices=GENDERS, max_length=10)
    # main admin in multiple acount schemas won't be filling the weight
    weight = models.PositiveIntegerField("Peso", blank=True, null=True) 
    quotes = models.BooleanField("Quotas", default=True)
    dojo = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    creation_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.id:  # Generate only if no ID exists
            self.id = generate_unique_nanoid(self.__class__.__name__, self._meta.app_label)

        super().save(*args, **kwargs)

    def __str__(self): 
        return "{} {}".format(self.first_name, self.last_name)


### Dojo model ###

class Dojo(models.Model):
    """
    Model that holds names to be used as usernames. 
    Can only be created when a 'main_admin' is created and can be linked.
    These same admin acounts can create these objects, and can only create usernames for themselves.
    The username for the admin acounts should not be listed here.
    """
    dojo = models.CharField("Dojo", max_length=99, unique=True)
    is_registered = models.BooleanField(default=False)
    mother_acount = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'main_admin'})

    def clean(self):
        if self.mother_acount.role != "main_admin":
            raise ValidationError({"mother_acount": "Mother account must be a main_admin."})
        
    def save(self, *args, **kwargs):
        if self.mother_acount.role != "main_admin":
            raise ValidationError("Mother account must be a main_admin.")
        
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.dojo


### Teams models ###

class Team(models.Model):

    id = models.CharField(primary_key=True, max_length=10, unique=True, editable=False)
    dojo = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    athlete1 = models.ForeignKey(Athlete, verbose_name="Atleta 1", related_name="first_element", on_delete=models.CASCADE)
    athlete2 = models.ForeignKey(Athlete, verbose_name="Atleta 2", related_name="second_element", on_delete=models.CASCADE)
    athlete3 = models.ForeignKey(Athlete, verbose_name="Atleta 3", related_name="third_element", on_delete=models.CASCADE, blank=True, null=True)
    athlete4 = models.ForeignKey(Athlete, verbose_name="Atleta 4", related_name="forth_element", on_delete=models.CASCADE, blank=True, null=True)
    athlete5 = models.ForeignKey(Athlete, verbose_name="Atleta 5", related_name="fifth_element", on_delete=models.CASCADE, blank=True, null=True)
    category = models.CharField("Escalão", max_length=99)
    match_type = models.CharField("Prova", choices=MATCHES, max_length=10)
    gender = models.CharField("Género", choices=GENDERS, max_length=10)
    team_number = models.IntegerField("Nº Equipa")
    competition = models.ForeignKey(Event, on_delete=models.CASCADE)
    creation_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.id:  # Generate only if no ID exists
            self.id = generate_unique_nanoid("Team", "registration")
        super().save(*args, **kwargs)

    def __str__(self):
        return "{} {} {}".format(self.match_type, self.category, self.gender)


### Classification models ###

class Classification(models.Model):
    competition = models.ForeignKey(Event, on_delete=models.CASCADE)
    first_place = models.ForeignKey(Athlete, verbose_name="Primeiro Classificado", related_name="first_place", on_delete=models.CASCADE)
    second_place = models.ForeignKey(Athlete, verbose_name="Segundo Classificado", related_name="second_place", on_delete=models.CASCADE, null=True, blank=True)
    third_place = models.ForeignKey(Athlete, verbose_name="Terceiro Classificado", related_name="third_place", on_delete=models.CASCADE, null=True, blank=True)

    def clean(self):
        super().clean()

        athletes = [self.first_place, self.second_place, self.third_place]
        athletes = [a for a in athletes if a is not None]

        if len(set(athletes)) != len(athletes):
            raise ValidationError("Each place must be assigned to a different athlete.")

        categories = {a.category for a in athletes}
        if len(categories) > 1:
            raise ValidationError("All athletes must belong to the same category.")
        
        genders = {a.gender for a in athletes}
        if len(genders) > 1:
            raise ValidationError("All athletes must belong to the same gender.")
        
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return "{} {} {} Classification".format(self.competition.name, self.first_place.category, self.first_place.gender.capitalize())


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