from django.db import models

from core.models import Category
from events.models import Discipline
from registration.models import Athlete
from core.constants import GENDERS

# Create your models here.

class Bracket(models.Model):

    DRAW_TYPE = {
        "Liga": "Liga",
        "Torneio/Finais": "Torneio/Finais",
        "Misto": "Torneio",
    }

    name = models.CharField("Prova", max_length=100)
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    # contender1 = models.ForeignKey(Athlete, verbose_name="Atleta 1", related_name="competitor1", on_delete=models.CASCADE)
    # contender2 = models.ForeignKey(Athlete, verbose_name="Atleta 2", related_name="competitor2", on_delete=models.CASCADE)
    type = models.CharField("Peso", choices=DRAW_TYPE, max_length=16, blank=True, null=True)
    gender = models.CharField("Género", choices=GENDERS, max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    

class Match(models.Model):
    bracket = models.ForeignKey(Bracket, on_delete=models.CASCADE, related_name="matches")
    athlete_red = models.ForeignKey(Athlete, on_delete=models.CASCADE, related_name="matches_as_red")
    athlete_blue = models.ForeignKey(Athlete, on_delete=models.CASCADE, related_name="matches_as_blue")
    round_number = models.IntegerField()
    match_number = models.IntegerField()
    winner = models.ForeignKey(Athlete, on_delete=models.SET_NULL, null=True, blank=True, related_name="won_matches")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['bracket', 'athlete_red', 'athlete_blue']

    def __str__(self):
        return f"{self.athlete_red} vs {self.athlete_blue} (Round {self.round_number})"