from rest_framework import serializers
import draw.models as models
from registration.serializers import CompactPersonSerializer


class BracketSerializer(serializers.ModelSerializer):
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
        exclude = ["match"]

        
class KumiteResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.KumiteResult
        exclude = ["match"]


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


class PatchMatchWinnerSerializer(serializers.Serializer):
    winner = serializers.ChoiceField(choices=[1, 2])