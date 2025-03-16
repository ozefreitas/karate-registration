from rest_framework import serializers
import registration.models as models


class AthletesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Athlete
        fields = "__all__"