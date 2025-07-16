from rest_framework import serializers
import draw.models as models


class BracketSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Bracket
        fields = "__all__"


class CreateBracketSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Bracket
        fields = "__all__"


class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Match
        fields = "__all__"


class CreateMatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Match
        fields = "__all__"