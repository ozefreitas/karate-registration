from rest_framework import serializers
import registration.models as models
from core.serializers import UsersSerializer
from dojos.utils.utils import calc_age
from registration.utils.utils import get_comp_age
from decouple import config
import datetime

### Athletes Serializer Classes 


class AthletesSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    dojo = UsersSerializer()

    class Meta:
        model = models.Athlete
        exclude = ("quotes", )
        
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_age(self, obj):
        """Normal Athlete table should display the real age at the time.
        Registration modals should display the corrected age."""
        year_of_birth = obj.birth_date.year
        date_now = datetime.datetime.now()
        age_at_comp = date_now.year - year_of_birth
        if (date_now.month, date_now.day) < (obj.birth_date.month, obj.birth_date.day):
            age_at_comp -= 1
        return age_at_comp


class CompactAthletesSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()

    class Meta:
        model = models.Athlete
        fields = ["id" ,"first_name", "last_name", "gender", "category"]
    
    def get_category(self, obj):
        """Sends the category of each athlete if a category is provided. 
        Categories comming from the context are only the ones linked to the respective Discipline"""
        
        categories = self.context.get('discipline_categories', [])
        current_age = get_comp_age(obj.birth_date)
        if categories == []:
            return None
        if current_age <= 0 or current_age is None:
            return None
        
        age_method = config('AGE_CALC_REF')
        event_age = current_age if age_method == "true" else calc_age(age_method, obj.birth_date)
        for category in categories:
            if category.min_age <= event_age <= category.max_age:
                return category.name
        return None


class NotAdminLikeTypeAthletesSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    
    class Meta:
        model = models.Athlete
        fields = "__all__"

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_age(self, obj):
        return get_comp_age(obj.birth_date)


class NotInEventAthletesSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    
    class Meta:
        model = models.Athlete
        fields = "__all__"

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_age(self, obj):
        age_method = config('AGE_CALC_REF')
        current_age = get_comp_age(obj.birth_date)
        event_age = current_age if age_method == "true" else calc_age(age_method, obj.birth_date)
        return event_age
    

class CreateAthleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Athlete
        exclude = ("age", "weight", )

    def validate(self, data):
        weight = data.get("weight")
        stundent = data.get("student")
        gender = data.get("gender")

        if stundent and weight != "":
            raise serializers.ValidationError({
                'incompatible_athlete': ["Alunos não têm peso associado."]
            })
    
        if gender not in ["Masculino", "Feminino"]:
            raise serializers.ValidationError({
                'impossible_gender': ['Género "Misto" apenas está disponível para Equipas.']
            })
    
        
        
        return data


class UpdateAthleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Athlete
        exclude = ("age", "dojo", "skip_number", )


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
    match_type = serializers.SerializerMethodField()
    team_size = serializers.SerializerMethodField()
    gender = serializers.SerializerMethodField()

    class Meta:
        model = models.Team
        fields = "__all__"
    
    def get_match_type(self, obj):
        return obj.match_type.capitalize() if obj.match_type else ''
    
    def get_athlete1_full_name(self, obj):
        return f"{obj.athlete1.first_name} {obj.athlete1.last_name}"
    
    def get_athlete2_full_name(self, obj):
        return f"{obj.athlete2.first_name} {obj.athlete2.last_name}"
    
    def get_athlete3_full_name(self, obj):
        return f"{obj.athlete3.first_name} {obj.athlete3.last_name}" if obj.athlete3 else None
    
    def get_team_size(self, obj):
        athletes = [obj.athlete1, obj.athlete2, obj.athlete3, obj.athlete4, obj.athlete5]
        return sum(1 for athlete in athletes if athlete is not None)
    
    def get_gender(self, obj):
        return obj.athlete1.gender.capitalize() if obj.athlete1.gender else ''
    

class UpdateTeamsSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = models.Team
        exclude = ("dojo", "team_number", "match_type", "category", "gender", "competition", )

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