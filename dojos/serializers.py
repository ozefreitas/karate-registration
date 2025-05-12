from rest_framework import serializers
from django.contrib.auth.models import User
import dojos.models as models


class CompetitionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CompetitionDetail
        fields = "__all__"


class CreateCompetitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CompetitionDetail
        exclude = ("id", "has_ended")


class UpdateCompetitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CompetitionDetail
        exclude = ("id", "has_ended")


class NotificationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Notification
        fields = "__all__"


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