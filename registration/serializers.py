from rest_framework import serializers
import registration.models as models


### Athletes Serializer Classes 

class AthletesSerializer(serializers.ModelSerializer):
    gender = serializers.SerializerMethodField()
    match_type = serializers.SerializerMethodField()
    category_index = serializers.SerializerMethodField()

    class Meta:
        model = models.Athlete
        fields = "__all__"

    def get_gender(self, obj):
        return obj.gender.capitalize() if obj.gender else ''
    
    def get_match_type(self, obj):
        return obj.match_type.capitalize() if obj.match_type else ''
    
    def get_category_index(self, obj):
        if obj.category.lower() == "infantil":
            return 1
        if obj.category.lower() == "inicado":
            return 2
        if obj.category.lower() == "juvenil":
            return 3
        if obj.category.lower() == "cadete":
            return 4
        if obj.category.lower() == "júnior":
            return 5
        if obj.category.lower() == "sénior":
            return 6
        if obj.category.lower() == "veterano +35":
            return 7
        if obj.category.lower() == "veterano +50":
            return 8


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
    athlete = CompactAthletesSerializer()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    gender = serializers.SerializerMethodField()
    match_type = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()

    class Meta:
        model = models.Individual
        fields = "__all__"

    def get_first_name(self, obj):
        return obj.athlete.first_name if obj.athlete.first_name else ''
    
    def get_last_name(self, obj):
        return obj.athlete.last_name if obj.athlete.last_name else ''

    def get_gender(self, obj):
        return obj.athlete.gender.capitalize() if obj.athlete.gender else ''
    
    def get_match_type(self, obj):
        return obj.athlete.match_type.capitalize() if obj.athlete.match_type else ''
    
    def get_category(self, obj):
        return obj.athlete.category if obj.athlete.category else ''


### Teams Serializer Classes

class TeamsSerializer(serializers.ModelSerializer):
    athlete1 = CompactAthletesSerializer()
    athlete1_full_name = serializers.SerializerMethodField()
    athlete2 = CompactAthletesSerializer()
    athlete2_full_name = serializers.SerializerMethodField()
    athlete3 = CompactAthletesSerializer()
    athlete3_full_name = serializers.SerializerMethodField()
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
    
    def get_athlete1_full_name(self, obj):
        return f"{obj.athlete1.first_name} {obj.athlete1.last_name}"
    
    def get_athlete2_full_name(self, obj):
        return f"{obj.athlete2.first_name} {obj.athlete2.last_name}"
    
    def get_athlete3_full_name(self, obj):
        return f"{obj.athlete3.first_name} {obj.athlete3.last_name}"
    

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