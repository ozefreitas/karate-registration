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
    

class CompactAthletesSerializer(serializers.ModelSerializer):
    gender = serializers.SerializerMethodField()
    match_type = serializers.SerializerMethodField()

    class Meta:
        model = models.Athlete
        fields = ["id" ,"first_name", "last_name", "gender", "match_type", "category"]

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
    athlete1 = CompactAthletesSerializer()
    athlete2 = CompactAthletesSerializer()
    athlete3 = CompactAthletesSerializer()
    athlete4 = CompactAthletesSerializer()
    athlete5 = CompactAthletesSerializer()
    gender = serializers.SerializerMethodField()
    match_type = serializers.SerializerMethodField()

    class Meta:
        model = models.Team
        fields = "__all__"
    
    def get_gender(self, obj):
        return obj.gender.capitalize() if obj.gender else ''
    
    def get_match_type(self, obj):
        return obj.match_type.capitalize() if obj.match_type else ''
    

### Dojos Serializer Classes

class DojosSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Dojo
        fields = "__all__"


### Classifications Serializer Classes

class AllClassificationsSerializer(serializers.ModelSerializer):
    competition = serializers.SerializerMethodField()
    full_category = serializers.SerializerMethodField()
    first_place = serializers.SerializerMethodField()
    second_place = serializers.SerializerMethodField()
    third_place = serializers.SerializerMethodField()

    def format_athlete_name(self, name: str) -> str:
        return name.lower().capitalize()

    class Meta:
        model = models.Classification
        fields = "__all__"

    def get_full_category(self, obj):
        return f"{obj.first_place.match_type.capitalize()} {obj.first_place.category} {obj.first_place.gender.capitalize()}"
    
    def get_competition(self, obj):
        return f"{obj.competition.name} {obj.competition.season}"
    
    def get_first_place(self, obj):
        return f"{self.format_athlete_name(obj.first_place.first_name)} {self.format_athlete_name(obj.first_place.last_name)}"
    
    def get_second_place(self, obj):
        return f"{self.format_athlete_name(obj.second_place.first_name)} {self.format_athlete_name(obj.second_place.last_name)}"
    
    def get_third_place(self, obj):
        return f"{self.format_athlete_name(obj.third_place.first_name)} {self.format_athlete_name(obj.third_place.last_name)}"
    

class ClassificationsSerializer(serializers.ModelSerializer):
    full_category = serializers.SerializerMethodField()
    first_place = CompactAthletesSerializer()
    second_place = CompactAthletesSerializer()
    third_place = CompactAthletesSerializer()

    class Meta:
        model = models.Classification
        exclude = ("competition", )

    def get_full_category(self, obj):
        return f"{obj.first_place.match_type.capitalize()} {obj.first_place.category} {obj.first_place.gender.capitalize()}"


class CreateClassificationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Classification
        fields = "__all__"