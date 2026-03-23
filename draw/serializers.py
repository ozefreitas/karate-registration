from rest_framework import serializers
import draw.models as models
from registration.serializers.base import CompactPersonSerializer
from core.serializers.categories import CompactCategorySerializer


class BracketSerializer(serializers.ModelSerializer):
    category = CompactCategorySerializer()
    class Meta:
        model = models.Bracket
        fields = "__all__"


class CreateBracketSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Bracket
        fields = "__all__"


class KataResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.KataResult
        exclude = ["match", "created_at"]

        
class KumiteResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.KumiteResult
        exclude = ["match", "created_at"]


class MatchSerializer(serializers.ModelSerializer):
    contender_1 = CompactPersonSerializer()
    contender_2 = CompactPersonSerializer()
    winner = CompactPersonSerializer()
    kataresult = KataResultSerializer(read_only=True, allow_null=True)
    kumiteresult = KumiteResultSerializer(read_only=True, allow_null=True)

    class Meta:
        model = models.Match
        fields = "__all__"


class CreateMatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Match
        fields = "__all__"


class UpdateMatchSerializer(serializers.ModelSerializer):
    kataresult = KataResultSerializer(required=False)

    class Meta:
        model = models.Match
        exclude = ["round_number", "match_number", "bracket"]
    
    def validate(self, data):
        instance = self.instance
        contender_1 = data.get("contender_1", instance.contender_1)
        contender_2 = data.get("contender_2", instance.contender_2)

        if data.get("ongoing") and contender_1 is None and contender_2 is None:
            raise serializers.ValidationError(
                "Partida não tem pelo menos um dos competidores definidos. Conclua as partidas das rondas anteriores!"
            )

        return data

    def update(self, instance, validated_data):
        kata_data = validated_data.pop("kataresult", None)

        # Update Match fields
        instance = super().update(instance, validated_data)

        # Update or create KataResult if data was provided
        if kata_data is not None:
            models.KataResult.objects.update_or_create(
                match=instance,
                defaults=kata_data,
            )

        return instance


class PatchMatchWinnerSerializer(serializers.Serializer):
    winner = serializers.ChoiceField(choices=[1, 2])


class AdvanceMatchSerializer(serializers.Serializer):
    next_match_id = serializers.CharField()


class PreviousMatchSerializer(serializers.Serializer):
    prev_match_id = serializers.CharField()