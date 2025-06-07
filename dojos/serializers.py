from rest_framework import serializers
from django.contrib.auth.models import User
import dojos.models as models
import registration.serializers 


class CompetitionsSerializer(serializers.ModelSerializer):
    individuals = registration.serializers.CompactAthletesSerializer(many=True)
    teams = registration.serializers.TeamsSerializer(many=True)
    
    class Meta:
        model = models.Event
        fields = "__all__"


class CreateCompetitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Event
        exclude = ("id", "has_ended")


class UpdateCompetitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Event
        exclude = ("id", "has_ended")


class NotificationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Notification
        fields = "__all__"


class AddAthleteSerializer(serializers.Serializer):
    athlete_id = serializers.CharField()


class AddTeamSerializer(serializers.Serializer):
    team_id = serializers.CharField()


class RegisterUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "username", "password"]
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            password=validated_data['password']
        )
        return user