from rest_framework import serializers
import dojos.models as models
from core.models import User
from registration.models import Dojo
import registration.serializers
import core.serializers
from django.utils.text import slugify
from .models import Event, Discipline
from datetime import date


class EventsSerializer(serializers.ModelSerializer):
    individuals = serializers.SerializerMethodField()
    is_open = serializers.SerializerMethodField()
    is_closed = serializers.SerializerMethodField()
    is_retification = serializers.SerializerMethodField()
    number_registrations = serializers.SerializerMethodField()
    
    class Meta:
        model = models.Event
        fields = "__all__"

    def get_individuals(self, obj):
        """Filters the athletes in the individuals fields based on que requesting user"""
        user = self.context['request'].user
        if not user.is_authenticated:
            return []
        if user.role == 'free_dojo' or user.role == 'subed_dojo':
            qs = obj.individuals.filter(dojo=user)
        elif user.role == 'main_admin' or user.role == 'superuser':
            qs = obj.individuals.all()
        else:
            return []
        return registration.serializers.CompactAthletesSerializer(qs, many=True).data
    
    def get_is_open(self, obj):
        if obj.has_registrations:
            today = date.today()
            if today >= obj.start_registration and today <= obj.retifications_deadline:
                return True
        return False
    
    def get_is_closed(self, obj):
        if obj.has_registrations:
            today = date.today()
            if today > obj.retifications_deadline:
                return True
        return False
    
    def get_is_retification(self, obj):
        if obj.has_registrations:
            today = date.today()
            if today > obj.end_registration and today <= obj.retifications_deadline:
                return True
        return False
    
    def get_number_registrations(self, obj):
        number = obj.individuals.count()
        disciplines = Discipline.objects.filter(event=obj)
        for discipline in disciplines:
            number += discipline.individuals.count()
        return number


class CreateEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Event
        exclude = ("has_ended", "individuals", "rating", )
    
    def validate(self, data):
        name = data.get("name")
        season = data.get("season")

        slug_id = slugify(f"{name} {season}")

        # Only check on create
        if not self.instance and Event.objects.filter(id=slug_id).exists():
            raise serializers.ValidationError({
                "id": ["Já existe um evento com esse nome nesta época."]
            })
        
        has_registrations = data.get('has_registrations')
        start = data.get('start_registration')
        end = data.get('end_registration')
        deadline = data.get('retifications_deadline')

        if has_registrations and (start is None or end is None or deadline is None):
            raise serializers.ValidationError({
                "non_field_errors": [
                    "Eventos com inscrições precisam de todas as datas."
                ]
            })

        return data


class UpdateEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Event
        exclude = ("id", "has_ended")


class DisciplinesSerializer(serializers.ModelSerializer):
    individuals = serializers.SerializerMethodField()
    teams = registration.serializers.TeamsSerializer(many=True)
    categories = core.serializers.CategorySerializer(many=True)
    
    class Meta:
        model = models.Discipline
        fields = "__all__"

    def get_individuals(self, obj):
        """Filters the athletes in the individuals fields based on que requesting user"""
        user = self.context['request'].user
        event = self.context['request'].query_params.get("event_disciplines")
        if not user.is_authenticated:
            return []
        if user.role == 'free_dojo' or user.role == 'subed_dojo':
            qs = obj.individuals.filter(dojo=user)
        elif user.role == 'main_admin' or user.role == 'superuser':
            qs = obj.individuals.all()
        else:
            return []
        
        return registration.serializers.CompactAthletesSerializer(qs,
                                                                   many=True, 
                                                                   context={
                                                                            **self.context,
                                                                            'discipline_categories': list(obj.categories.filter()),
                                                                            'event_id': event
                                                                        }).data


class DisciplinesCompactSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Discipline
        fields = ["id", "name"]


class CreateDisciplineSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Discipline
        exclude = ["individuals", "teams", ]


class UpdateDisciplineSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Discipline
        exclude = ["id", ]


class NotificationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Notification
        fields = "__all__"

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["dojo"].queryset = models.User.objects.filter(role__in=["free_dojo", "subed_dojo"])


class AddAthleteSerializer(serializers.Serializer):
    athlete_id = serializers.CharField()
    event_id = serializers.CharField()


class DeleteAthleteSerializer(serializers.Serializer):
    athlete_id = serializers.CharField()


class AddCategorySerializer(serializers.Serializer):
    category_id = serializers.CharField()


class AddTeamSerializer(serializers.Serializer):
    team_id = serializers.CharField()


class RatingSerializer(serializers.Serializer):
    rating_signal = serializers.IntegerField()


class DojosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dojo
        fields = "__all__"


class CreateDojosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dojo
        exclude = ["is_registered", ]