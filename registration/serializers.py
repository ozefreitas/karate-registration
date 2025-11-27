from rest_framework import serializers
import registration.models as models
from core.serializers.users import UsersSerializer
from core.utils.utils import calc_age
from events.models import Event
from registration.utils.utils import get_comp_age
from decouple import config
import datetime

### Members Serializer Classes 


class MembersSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    club = UsersSerializer()

    class Meta:
        model = models.Member
        exclude = ("quotes_legible", "creation_date", "favorite", "graduation", "id_number", "weight", "birth_date")

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_age(self, obj):
        """Normal Member table should display the real age at the time.
        Registration modals should display the corrected age."""
        year_of_birth = obj.birth_date.year
        date_now = datetime.datetime.now()
        age_at_comp = date_now.year - year_of_birth
        if (date_now.month, date_now.day) < (obj.birth_date.month, obj.birth_date.day):
            age_at_comp -= 1
        return age_at_comp


class CompactMembersSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    club = serializers.SerializerMethodField()

    class Meta:
        model = models.Member
        fields = ["id" ,"first_name", "last_name", "gender", "club", "full_name"]

    def get_club(self, obj):
        return obj.club.username
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class CompactCategorizedMembersSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    club = serializers.SerializerMethodField()

    class Meta:
        model = models.Member
        fields = ["id", "first_name", "last_name", "gender", "category", "club", "full_name"]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        drop = self.context.get("restricted", [])

        if drop == "true":
            self.fields.pop("id", None)

    def get_club(self, obj):
        return obj.club.username
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    
    def get_category(self, obj):
        """Sends the category of each member if a category is provided. 
        Categories comming from the context are only the ones linked to the respective Discipline"""
        
        categories = self.context.get('discipline_categories', [])
        event_id = self.context['request'].query_params.get("event_disciplines")
        try:
            event = Event.objects.get(id=event_id)
            season = event.season.split("/")[0]
        except Event.DoesNotExist:
            raise serializers.ValidationError("Event does not exist")
        
        current_age = get_comp_age(obj.birth_date)
        if categories == []:
            return None
        if current_age <= 0 or current_age is None:
            return None
        
        age_method = config('AGE_CALC_REF')
        event_age = current_age if age_method == "true" else calc_age(age_method, obj.birth_date, season)
        for category in categories:
            if category.gender == obj.gender:
                if category.min_age <= event_age <= category.max_age:

                    if obj.weight is not None:
                        if category.min_weight is not None and category.max_weight is not None:
                            if category.min_weight <= obj.weight <= category.max_weight:
                                return f'{category.name} +{category.max_weight}'
                            else:
                                continue
                        if category.max_weight is not None:
                            if obj.weight < category.max_weight:
                                return f'{category.name} -{category.max_weight}'
                        elif category.min_weight is not None:
                            if obj.weight >= category.min_weight:
                                return f'{category.name} +{category.min_weight}'
                        else:
                            return category.name
                    else:
                        return category.name
        return None


class NotAdminLikeTypeMembersSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    monthly_payment_status = serializers.SerializerMethodField()
    
    class Meta:
        model = models.Member
        exclude = ("creation_date", )

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_age(self, obj):
        return get_comp_age(obj.birth_date)
    
    def get_monthly_payment_status(self, obj):
        return obj.current_month_payment()


class AdminLikeTypeMembersSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()

    class Meta:
        model = models.Member
        exclude = ("quotes_legible", "creation_date", "favorite", "club")

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_age(self, obj):
        """Normal Member table should display the real age at the time.
        Registration modals should display the corrected age."""
        year_of_birth = obj.birth_date.year
        date_now = datetime.datetime.now()
        age_at_comp = date_now.year - year_of_birth
        if (date_now.month, date_now.day) < (obj.birth_date.month, obj.birth_date.day):
            age_at_comp -= 1
        return age_at_comp


class NotInEventMembersSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    
    class Meta:
        model = models.Member
        exclude = ["creation_date", "quotes", "favorite", "member_type"]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_age(self, obj):
        event_id = self.context['request'].query_params.get("not_in_event")

        try:
            event = Event.objects.get(id=event_id)
            season = event.season.split("/")[0]
        except Event.DoesNotExist:
            raise serializers.ValidationError("Event does not exist")
        
        age_method = config('AGE_CALC_REF')
        current_age = get_comp_age(obj.birth_date)
        event_age = current_age if age_method == "true" else calc_age(age_method, obj.birth_date, season)
        return event_age
    

class ClubsCreateMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Member
        fields = "__all__"
        read_only_fields = ("club", ) 

    def validate(self, data):
        weight = data.get("weight")
        stundent = data.get("student")
        gender = data.get("gender")

        if stundent and weight != "":
            raise serializers.ValidationError({
                'incompatible_member': ["Alunos não têm peso associado."]
            })
    
        if gender not in ["Masculino", "Feminino"]:
            raise serializers.ValidationError({
                'impossible_gender': ['Género "Misto" apenas está disponível para Equipas.']
            })
      
        return data
    

class AdminCreateMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Member
        exclude = ("address", "post_code", "national_card_number", "taxpayer_number")

    def validate(self, data):
        weight = data.get("weight")
        stundent = data.get("student")
        gender = data.get("gender")

        if stundent and weight != "":
            raise serializers.ValidationError({
                'incompatible_member': ["Alunos não têm peso associado."]
            })
    
        if gender not in ["Masculino", "Feminino"]:
            raise serializers.ValidationError({
                'impossible_gender': ['Género "Misto" apenas está disponível para Equipas.']
            })
      
        return data


class UpdateMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Member
        exclude = ("club", "id_number", "created_by", "creation_date")


### Monthly Payments Serializer Classes

class MonthlyMemberPaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.MonthlyMemberPayment
        fields = "__all__"


### Teams Serializer Classes

class TeamsSerializer(serializers.ModelSerializer):
    member1 = CompactMembersSerializer()
    member1_full_name = serializers.SerializerMethodField()
    member2 = CompactMembersSerializer()
    member2_full_name = serializers.SerializerMethodField()
    member3 = CompactMembersSerializer()
    member3_full_name = serializers.SerializerMethodField()
    member4 = CompactMembersSerializer()
    member5 = CompactMembersSerializer()
    match_type = serializers.SerializerMethodField()
    team_size = serializers.SerializerMethodField()
    gender = serializers.SerializerMethodField()

    class Meta:
        model = models.Team
        fields = "__all__"
    
    def get_match_type(self, obj):
        return obj.match_type.capitalize() if obj.match_type else ''
    
    def get_member1_full_name(self, obj):
        return f"{obj.member1.first_name} {obj.member1.last_name}"
    
    def get_member2_full_name(self, obj):
        return f"{obj.member2.first_name} {obj.member2.last_name}"
    
    def get_member3_full_name(self, obj):
        return f"{obj.member3.first_name} {obj.member3.last_name}" if obj.member3 else None
    
    def get_team_size(self, obj):
        members = [obj.member1, obj.member2, obj.member3, obj.member4, obj.member5]
        return sum(1 for member in members if member is not None)
    
    def get_gender(self, obj):
        return obj.member1.gender.capitalize() if obj.member1.gender else ''
    

class UpdateTeamsSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = models.Team
        exclude = ("club", "team_number", "match_type", "category", "gender", "competition", )


### Classifications Serializer Classes

class AllClassificationsSerializer(serializers.ModelSerializer):
    competition = serializers.SerializerMethodField()
    full_category = serializers.SerializerMethodField()
    first_place = serializers.SerializerMethodField()
    second_place = serializers.SerializerMethodField()
    third_place = serializers.SerializerMethodField()

    def format_member_name(self, name: str) -> str:
        return name.lower().capitalize()

    class Meta:
        model = models.Classification
        fields = "__all__"

    def get_full_category(self, obj):
        return f"{obj.first_place.match_type.capitalize()} {obj.first_place.category} {obj.first_place.gender.capitalize()}"
    
    def get_competition(self, obj):
        return f"{obj.competition.name} {obj.competition.season}"
    
    def get_first_place(self, obj):
        return f"{self.format_member_name(obj.first_place.first_name)} {self.format_member_name(obj.first_place.last_name)}"
    
    def get_second_place(self, obj):
        return f"{self.format_member_name(obj.second_place.first_name)} {self.format_member_name(obj.second_place.last_name)}"
    
    def get_third_place(self, obj):
        return f"{self.format_member_name(obj.third_place.first_name)} {self.format_member_name(obj.third_place.last_name)}"
    

class ClassificationsSerializer(serializers.ModelSerializer):
    full_category = serializers.SerializerMethodField()
    first_place = CompactMembersSerializer()
    second_place = CompactMembersSerializer()
    third_place = CompactMembersSerializer()

    class Meta:
        model = models.Classification
        exclude = ("competition", )

    def get_full_category(self, obj):
        return f"{obj.first_place.match_type.capitalize()} {obj.first_place.category} {obj.first_place.gender.capitalize()}"


class CreateClassificationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Classification
        fields = "__all__"