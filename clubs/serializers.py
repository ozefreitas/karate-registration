from rest_framework import serializers
from .models import Club


class RatingSerializer(serializers.Serializer):
    rating_signal = serializers.IntegerField()


class ClubsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Club
        fields = "__all__"


class CreateClubSerializer(serializers.ModelSerializer):
    class Meta:
        model = Club
        exclude = ["is_registered", "mother_acount"]