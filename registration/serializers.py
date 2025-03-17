from rest_framework import serializers
import registration.models as models


### Athletes Serializer Classes 

class AthletesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Athlete
        fields = "__all__"

class CreateAthleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Athlete
        exclude = ("age", "dojo", )

class UpdateAthleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Athlete
        exclude = ("age", "dojo", )


### Dojos Serializer Classes

class DojosSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Dojo
        fields = "__all__"