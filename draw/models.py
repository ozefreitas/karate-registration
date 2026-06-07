from django.db import models

from core.models import Category, Event
from events.models import Discipline
from registration.models import Person, Team
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
    officialized_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.name} - {self.event.name} {self.event.season}'
    

class Match(models.Model):
    bracket = models.ForeignKey(Bracket, on_delete=models.CASCADE, related_name="matches")
    # Individuals
    contender_1 = models.ForeignKey(Person, null=True, blank=True, on_delete=models.SET_NULL, related_name="matches_as_contender_1")
    contender_2 = models.ForeignKey(Person, null=True, blank=True, on_delete=models.SET_NULL, related_name="matches_as_contender_2")
    winner = models.ForeignKey(Person, null=True, blank=True, on_delete=models.SET_NULL, related_name="matches_won")
    round_number = models.IntegerField()
    is_third_place = models.BooleanField(default=False)
    loser_goes_to = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='loser_feeders'
    )
    feeds_into_scoring = models.ForeignKey(
        'ScoringRound', null=True, blank=True, on_delete=models.SET_NULL
    )
    match_number = models.IntegerField()
    # Teams
    team_contender_1 = models.ForeignKey(Team, null=True, blank=True, on_delete=models.SET_NULL, related_name="matches_as_contender_1")
    team_contender_2 = models.ForeignKey(Team, null=True, blank=True, on_delete=models.SET_NULL, related_name="matches_as_contender_2")
    team_winner = models.ForeignKey(Team, null=True, blank=True, on_delete=models.SET_NULL, related_name="matches_won")
    ongoing = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['bracket', 'contender_1', 'contender_2']

    @property
    def is_final(self):
        return self.round_number == 0 and self.match_number == 1 and not self.is_third_place


    def _get_winner(self):
        return self.team_winner if self.bracket.discipline.is_team else self.winner


    def _get_contender(self, number):
        if self.bracket.discipline.is_team:
            return self.team_contender_1 if number == 1 else self.team_contender_2
        return self.contender_1 if number == 1 else self.contender_2


    def _get_loser(self):
        winner = self._get_winner()
        c1 = self._get_contender(1)
        c2 = self._get_contender(2)
        return c2 if winner == c1 else c1


    def set_winner(self, winner):
        if winner not in [1, 2]:
            raise ValueError("Winner must be either 1 or 2.")

        if self.bracket.discipline.is_team:
            self.team_winner = self.team_contender_1 if winner == 1 else self.team_contender_2
        else:
            self.winner = self.contender_1 if winner == 1 else self.contender_2
        self.save()

        if not self.is_third_place:
            self.advance_winner()
            self.advance_loser()


    def advance_winner(self):
        winner = self._get_winner()
        if not winner:
            return

        # Finals: just close the match, no one to advance
        if self.is_final:
            self.ongoing = False
            self.save()
            return

        bracket = self.bracket
        current_round = self.round_number
        current_match_number = self.match_number

        if self.feeds_into_scoring is not None:
            entry = ScoringEntry.objects.filter(
                scoring_round=self.feeds_into_scoring,
                person__isnull=True
            ).first()
            
            if entry:
                entry.person = self.winner
                entry.save()

        else:
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
                return

            if self.bracket.discipline.is_team:
                if not pair_match.team_winner:
                    return
            else:
                if not pair_match.winner:
                    return

            next_round = current_round - 1
            next_match_number = (min(current_match_number, pair_number) + 1) // 2

            next_match, _ = Match.objects.get_or_create(
                bracket=bracket,
                round_number=next_round,
                match_number=next_match_number,
                defaults={
                    "contender_1": None, 
                    "contender_2": None,
                    "team_contender_1": None,
                    "team_contender_2": None
                }
            )

            if is_first_in_pair:
                if self.bracket.discipline.is_team:
                    next_match.team_contender_1 = self.team_winner
                    next_match.team_contender_2 = pair_match.team_winner
                else:
                    next_match.contender_1 = self.winner
                    next_match.contender_2 = pair_match.winner
            else:
                if self.bracket.discipline.is_team:
                    next_match.team_contender_1 = pair_match.team_winner
                    next_match.team_contender_2 = self.team_winner
                else:
                    next_match.contender_1 = pair_match.winner
                    next_match.contender_2 = self.winner

            next_match.save()


    def advance_loser(self):
        """
        When this match gets a winner (and thus a loser),
        advance the loser to the 3rd place match if one is linked.
        """
        winner = self._get_winner()
        if not winner:
            return

        # Determine the loser (or for indiv or team)
        loser = self._get_loser()
        # if self.contender_1 == self.winner:
        #     loser = self.contender_2
        # else:
        #     loser = self.contender_1
        if not loser:
            return

        if not self.loser_goes_to:
            return

        third_place_match = self.loser_goes_to

        # Check if the other semi-final has already placed its loser
        if self.bracket.discipline.is_team:
            if not third_place_match.team_contender_1:
                third_place_match.team_contender_1 = loser
            else:
                third_place_match.team_contender_2 = loser
        else:
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


class ScoringRound(models.Model):
    bracket = models.ForeignKey(Bracket, on_delete=models.CASCADE, related_name="scoring_rounds")
    round_number = models.IntegerField(default=0)
    is_final = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.bracket.discipline.name} {self.bracket.category.name} {self.bracket.category.gender} Finals'


class ScoringEntry(models.Model):
    scoring_round = models.ForeignKey(ScoringRound, on_delete=models.CASCADE, related_name="entries")
    person = models.ForeignKey(Person, null=True, blank=True, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, null=True, blank=True, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    rank = models.IntegerField(null=True, blank=True)
    entry_number = models.PositiveIntegerField()
    ongoing = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def recalculate_ranks(self):
        """Recalculate ranks for all entries in the same scoring round."""
        entries = ScoringEntry.objects.filter(
            scoring_round=self.scoring_round,
            score__isnull=False  # only rank entries that have a score
        ).order_by("-score")

        for rank, entry in enumerate(entries, start=1):
            entry.rank = rank
            entry.save()
            

    def set_ongoing(self):
        ScoringEntry.objects.filter(scoring_round=self.scoring_round, ongoing=True).update(ongoing=False)
        self.ongoing = True
        self.save(update_fields=["ongoing"])


    def __str__(self):
        if self.person != None:
            return f'{self.scoring_round.bracket.discipline.name} {self.scoring_round.bracket.category.name} {self.scoring_round.bracket.category.gender} Finals - {self.person.first_name} {self.person.last_name} ({self.person.club.username})'
        else:
            return f'{self.scoring_round.bracket.discipline.name} {self.scoring_round.bracket.category.name} {self.scoring_round.bracket.category.gender} Finals - TBD'
    

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


class ScoringResult(models.Model):
    scoring_entry = models.OneToOneField(
        ScoringEntry, 
        on_delete=models.CASCADE, 
        related_name='scoring_result'
    )
    kata = models.CharField("Kata", max_length=24, choices=KATAS, default="none", blank=True)
    score_1 = models.FloatField()
    score_2 = models.FloatField()
    score_3 = models.FloatField()
    score_4 = models.FloatField()
    score_5 = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
