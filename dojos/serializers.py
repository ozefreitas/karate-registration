from rest_framework import serializers
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
