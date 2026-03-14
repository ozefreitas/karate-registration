from django.db import models

from core.models import Category, Event
from events.models import Discipline
from registration.models import Person
from core.constants import KATAS

# Create your models here.

class Bracket(models.Model):

    DRAW_TYPES = {
        "Liga": "Liga",
        "Torneio/Finais": "Torneio/Finais",
        "Misto": "Torneio + Final de 8",
    }

    name = models.CharField("Prova", max_length=100)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, verbose_name="Evento", related_name="brackets")
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE, verbose_name="Modalidade")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Escalão")
    draw_type = models.CharField("Tipo", choices=DRAW_TYPES, max_length=16, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} - {self.event.name} {self.event.season}'
    

class Match(models.Model):
    bracket = models.ForeignKey(Bracket, on_delete=models.CASCADE, related_name="matches")
    contender_1 = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="matches_as_1", null=True)
    contender_2 = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="matches_as_2", null=True)
    round_number = models.IntegerField()
    is_third_place = models.BooleanField(default=False)
    loser_goes_to = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='loser_feeders'
    )
    match_number = models.IntegerField()
    winner = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True, related_name="won_matches")
    ongoing = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['bracket', 'contender_1', 'contender_2']

    def set_winner(self, winner):
        if winner not in [1, 2]:
            raise ValueError("Winner must be either 1 or 2.")

        self.winner = self.contender_1 if winner == 1 else self.contender_2
        self.save()

        self.advance_winner()
        self.advance_loser()
    
    def advance_winner(self):
        """
        When this match gets a winner,
        try to create/update next round match.
        """
        if not self.winner:
            return

        bracket = self.bracket
        current_round = self.round_number
        current_match_number = self.match_number

        # find paired match
        if current_match_number % 2 == 1:
            pair_number = current_match_number + 1
            is_first_in_pair = True
        else:
            pair_number = current_match_number - 1
            is_first_in_pair = False

        try:
            pair_match = Match.objects.get(
                bracket=bracket,
                round_number=current_round,
                match_number=pair_number
            )
        except Match.DoesNotExist:
            return  # no pair yet

        # only continue if both matches have winners
        if not pair_match.winner:
            return

        # next round info
        next_round = current_round - 1
        next_match_number = (min(current_match_number, pair_number) + 1) // 2

        # Gets the match
        next_match, _ = Match.objects.get_or_create(
            bracket=bracket,
            round_number=next_round,
            match_number=next_match_number,
            defaults={
                "contender_1": None,
                "contender_2": None,
            }
        )

        # assign contenders
        if is_first_in_pair:
            next_match.contender_1 = self.winner
            next_match.contender_2 = pair_match.winner
        else:
            next_match.contender_1 = pair_match.winner
            next_match.contender_2 = self.winner

        next_match.save()

    def advance_loser(self):
        """
        When this match gets a winner (and thus a loser),
        advance the loser to the 3rd place match if one is linked.
        """
        if not self.winner:
            return

        # Determine the loser
        if self.contender_1 == self.winner:
            loser = self.contender_2
        else:
            loser = self.contender_1

        if not loser:
            return

        if not self.loser_goes_to:
            return

        third_place_match = self.loser_goes_to

        # Check if the other semi-final has already placed its loser
        if not third_place_match.contender_1:
            third_place_match.contender_1 = loser
        else:
            third_place_match.contender_2 = loser

        third_place_match.save()
    
    def set_ongoing(self):
        Match.objects.filter(bracket=self.bracket, ongoing=True).update(ongoing=False)
        self.ongoing = True
        self.save(update_fields=["ongoing"])

    def __str__(self):
        return f'{self.bracket.discipline.name} {self.bracket.category.name} {self.bracket.category.gender} | {self.contender_1.first_name if self.contender_1 is not None else "bye"} {self.contender_1.last_name if self.contender_1 is not None else ""} vs {self.contender_2.first_name if self.contender_2 is not None else "bye"} {self.contender_2.last_name if self.contender_2 is not None else ""} | (Round {self.round_number})'

    
class MatchResult(models.Model):
    match = models.OneToOneField(
        Match, 
        on_delete=models.CASCADE, 
        related_name='%(class)s'  # becomes 'kataresult' and 'kumiteresult'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class KataResult(MatchResult):
    flags_contender_1 = models.PositiveSmallIntegerField("Bandeiras Atleta 1")
    flags_contender_2 = models.PositiveSmallIntegerField("Bandeiras Atleta 2")
    kata_contender_1 = models.CharField("Kata Atleta 1", max_length=24, choices=KATAS, default="none", blank=True)
    kata_contender_2 = models.CharField("Kata Atleta 2", max_length=24, choices=KATAS, default="none", blank=True)


class KumiteResult(MatchResult):
    points_contender_1 = models.PositiveSmallIntegerField(default=0)
    points_contender_2 = models.PositiveSmallIntegerField(default=0)
    points_conceded_contender_1 = models.PositiveSmallIntegerField(default=0)
    points_conceded_contender_2 = models.PositiveSmallIntegerField(default=0)


class FoulType(models.Model):
    name = models.CharField(max_length=50)
    penalty_points = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.name


class KumiteFoul(models.Model):
    result = models.ForeignKey(KumiteResult, on_delete=models.CASCADE, related_name='fouls')
    contender = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='fouls')
    foul_type = models.ForeignKey(FoulType, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)