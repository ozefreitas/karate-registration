from django.db import models

from core.models import Category, Event
from events.models import Discipline
from registration.models import Member
from core.constants import GENDERS

# Create your models here.

class Bracket(models.Model):

    DRAW_TYPES = {
        "Liga": "Liga",
        "Torneio/Finais": "Torneio/Finais",
        "Misto": "Torneio",
    }

    name = models.CharField("Prova", max_length=100)
    event=models.ForeignKey(Event, on_delete=models.CASCADE, verbose_name="Evento")
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE, verbose_name="Modalidade")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Escalão")
    draw_type = models.CharField("Tipo", choices=DRAW_TYPES, max_length=16, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    

class Match(models.Model):
    bracket = models.ForeignKey(Bracket, on_delete=models.CASCADE, related_name="matches")
    contender_1 = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="matches_as_1", null=True)
    contender_2 = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="matches_as_2", null=True)
    round_number = models.IntegerField()
    match_number = models.IntegerField()
    winner = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True, related_name="won_matches")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['bracket', 'contender_1', 'contender_2']

    def __str__(self):
        return f"{self.contender_1} vs {self.contender_2} (Round {self.round_number})"