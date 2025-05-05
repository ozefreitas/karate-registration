from rest_framework import serializers
import registration.models as models


### Athletes Serializer Classes 

class AthletesSerializer(serializers.ModelSerializer):
    gender = serializers.SerializerMethodField()
    match_type = serializers.SerializerMethodField()

    class Meta:
        model = models.Athlete
        fields = "__all__"

    def get_gender(self, obj):
        return obj.gender.capitalize() if obj.gender else ''
    
    def get_match_type(self, obj):
        return obj.match_type.capitalize() if obj.match_type else ''

class CreateAthleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Athlete
        exclude = ("age", "dojo", )

class UpdateAthleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Athlete
        exclude = ("age", "dojo", )


### Individuals Serializer Classes

class IndividualsSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Individual
        fields = "__all__"


### Teams Serializer Classes

class TeamsSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Team
        fields = "__all__"
    

### Dojos Serializer Classes

class DojosSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Dojo
        fields = "__all__"