from rest_framework import serializers
import draw.models as models
from events.models import EventDorsal
from registration.serializers.base import CompactPersonSerializer, CompactTeamSerializer
from core.serializers.categories import CompactCategorySerializer


class BracketSerializer(serializers.ModelSerializer):
    category = CompactCategorySerializer()
    is_team = serializers.SerializerMethodField()
    has_only_scoring_rounds = serializers.SerializerMethodField()

    class Meta:
        model = models.Bracket
        fields = "__all__"
    
    def get_is_team(self, obj):
        return obj.discipline.is_team
    
    def get_has_only_scoring_rounds(self, obj):
        return obj.scoring_rounds.exists() and not obj.matches.exists()


class CreateBracketSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Bracket
        fields = "__all__"


class KataResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.KataResult
        exclude = ["match", "created_at"]


class FoulTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.FoulType
        fields = ["id", "name", "penalty_points"]


class KumiteFoulSerializer(serializers.ModelSerializer):
    foul_type = FoulTypeSerializer(read_only=True)

    class Meta:
        model = models.KumiteFoul
        fields = ["id", "foul_type"]

        
class KumiteResultSerializer(serializers.ModelSerializer):
    fouls_contender_1 = serializers.SerializerMethodField()
    fouls_contender_2 = serializers.SerializerMethodField()

    class Meta:
        model = models.KumiteResult
        exclude = ["match", "created_at"]

    def get_fouls_contender_1(self, obj):
        fouls = [f for f in obj.fouls.all() if f.contender_id == obj.match.contender_1_id]
        return KumiteFoulSerializer(fouls, many=True).data

    def get_fouls_contender_2(self, obj):
        fouls = [f for f in obj.fouls.all() if f.contender_id == obj.match.contender_2_id]
        return KumiteFoulSerializer(fouls, many=True).data


class MatchSerializer(serializers.ModelSerializer):
    contender_1 = CompactPersonSerializer()
    contender_2 = CompactPersonSerializer()
    winner = CompactPersonSerializer()
    team_contender_1 = CompactTeamSerializer()
    team_contender_2 = CompactTeamSerializer()
    team_winner = CompactTeamSerializer()
    kataresult = KataResultSerializer(read_only=True, allow_null=True)
    kumiteresult = KumiteResultSerializer(read_only=True, allow_null=True)
    contender_1_dorsal = serializers.SerializerMethodField()
    contender_2_dorsal = serializers.SerializerMethodField()
    team_contender_1_dorsals = serializers.SerializerMethodField()
    team_contender_2_dorsals = serializers.SerializerMethodField()
    
    class Meta:
        model = models.Match
        fields = "__all__"

    def _get_dorsal(self, person):
        if not person:
            return None
        dorsals = self.context.get("dorsals", {})
        dorsal = dorsals.get(person.id)
        if dorsal is None:
            return None
        return str(dorsal).zfill(3)

    def _get_team_dorsals(self, team):
        if not team:
            return {}
        athletes = {
            "athlete1": team.athlete1,
            "athlete2": team.athlete2,
            "athlete3": team.athlete3,
            "athlete4": team.athlete4,
            "athlete5": team.athlete5,
        }
        return {
            slot: self._get_dorsal(athlete)
            for slot, athlete in athletes.items()
            if athlete is not None
        }

    def get_contender_1_dorsal(self, obj):
        return self._get_dorsal(obj.contender_1)

    def get_contender_2_dorsal(self, obj):
        return self._get_dorsal(obj.contender_2)

    def get_team_contender_1_dorsals(self, obj):
        return self._get_team_dorsals(obj.team_contender_1)

    def get_team_contender_2_dorsals(self, obj):
        return self._get_team_dorsals(obj.team_contender_2)


class CreateMatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Match
        fields = "__all__"


class UpdateMatchSerializer(serializers.ModelSerializer):
    kataresult = KataResultSerializer(required=False)
    kumiteresult = KumiteResultSerializer(required=False)

    class Meta:
        model = models.Match
        exclude = ["round_number", "match_number", "bracket"]
    
    def validate(self, data):
        instance = self.instance
        is_team = instance.bracket.discipline.is_team
        contender_1 = data.get("contender_1", instance.contender_1)
        contender_2 = data.get("contender_2", instance.contender_2)
        team_contender_1 = data.get("team_contender_1", instance.team_contender_1)
        team_contender_2 = data.get("team_contender_2", instance.team_contender_2)

        if data.get("ongoing") and not is_team and contender_1 is None and contender_2 is None:
            raise serializers.ValidationError(
                "Partida não tem pelo menos um dos competidores definidos. Conclua as partidas das rondas anteriores!"
            )

        if data.get("ongoing") and is_team and team_contender_1 is None and team_contender_2 is None:
            raise serializers.ValidationError(
                "Partida não tem pelo menos um dos competidores definidos. Conclua as partidas das rondas anteriores!"
            )

        return data

    def update(self, instance, validated_data):
        kata_data = validated_data.pop("kataresult", None)
        kumite_data = validated_data.pop("kumiteresult", None)

        # Update Match fields
        instance = super().update(instance, validated_data)

        # Update or create KataResult if data was provided
        if kata_data is not None:
            models.KataResult.objects.update_or_create(
                match=instance,
                defaults=kata_data,
            )
        
        # Update or create KumiteResult if data was provided
        if kumite_data is not None:
            models.KumiteResult.objects.update_or_create(
                match=instance,
                defaults=kumite_data,
            )

        return instance


class PatchMatchWinnerSerializer(serializers.Serializer):
    winner = serializers.ChoiceField(choices=[1, 2])


class AdvanceMatchSerializer(serializers.Serializer):
    next_match_id = serializers.CharField()


class PreviousMatchSerializer(serializers.Serializer):
    prev_match_id = serializers.CharField()


class ScoringResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ScoringResult
        exclude = ["scoring_entry", "created_at"]


class ScoringEntrySerializer(serializers.ModelSerializer):
    person = CompactPersonSerializer()
    team = CompactTeamSerializer()
    scoring_result = ScoringResultSerializer(read_only=True, allow_null=True)
    person_dorsal = serializers.SerializerMethodField()
    team_dorsal = serializers.SerializerMethodField()

    class Meta:
        model = models.ScoringEntry
        fields = "__all__"
    
    def _get_dorsal(self, person):
        if not person:
            return None
        dorsals = self.context.get("dorsals", {})
        dorsal = dorsals.get(person.id)
        if dorsal is None:
            return None
        return str(dorsal).zfill(3)
    
    def _get_team_dorsals(self, team):
        if not team:
            return {}
        athletes = {
            "athlete1": team.athlete1,
            "athlete2": team.athlete2,
            "athlete3": team.athlete3,
            "athlete4": team.athlete4,
            "athlete5": team.athlete5,
        }
        return {
            slot: self._get_dorsal(athlete)
            for slot, athlete in athletes.items()
            if athlete is not None
        }

    def get_person_dorsal(self, obj):
        return self._get_dorsal(obj.person)
    
    def get_team_dorsal(self, obj):
        return self._get_team_dorsals(obj.team)


class CreateScoringEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ScoringEntry
        fields = "__all__"


class UpdateScoringEntrySerializer(serializers.ModelSerializer):
    scoring_result = ScoringResultSerializer(required=False)

    class Meta:
        model = models.ScoringEntry
        exclude = ["scoring_round", "entry_number", "id"]
    
    def validate(self, data):
        instance = self.instance
        person = data.get("person", instance.person)
        team = data.get("team", instance.team)

        if data.get("ongoing") and person is None and team is None:
            raise serializers.ValidationError(
                "Partida não tem um Atleta/Equipa associado(a)! Conclua a partida anterior."
            )

        return data

    def update(self, instance, validated_data):
        scoring_result_data = validated_data.pop("scoring_result", None)

        if scoring_result_data is not None:
            scores = [
                scoring_result_data.get("score_1", 0),
                scoring_result_data.get("score_2", 0),
                scoring_result_data.get("score_3", 0),
                scoring_result_data.get("score_4", 0),
                scoring_result_data.get("score_5", 0),
            ]

            scores.remove(min(scores))
            scores.remove(max(scores))
            total = sum(scores)

            validated_data["score"] = total

        instance = super().update(instance, validated_data)

        if scoring_result_data is not None:
            models.ScoringResult.objects.update_or_create(
                scoring_entry=instance,
                defaults=scoring_result_data,
            )
            instance.recalculate_ranks()  # recalculate after score is saved

        return instance