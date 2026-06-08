from rest_framework import serializers
from registration.models import Person, Team
from registration.utils.utils import get_comp_age


class CompactPersonSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    club = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()

    class Meta:
        model = Person
        fields = ["id", "gender", "club", "full_name", "age", "weight", "graduation"]

    def get_club(self, obj):
        return obj.club.username
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    
    def get_age(self, obj):
        return get_comp_age(obj.birth_date)
    

class CompactTeamSerializer(serializers.ModelSerializer):
    athlete1 = CompactPersonSerializer()
    athlete2 = CompactPersonSerializer()
    athlete3 = CompactPersonSerializer()
    athlete4 = CompactPersonSerializer()
    athlete5 = CompactPersonSerializer()
    club = serializers.SerializerMethodField()

    class Meta:
        model = Team
        exclude = ["creation_date", "modified_date", "category"]

    def get_club(self, obj):
        return obj.club.username