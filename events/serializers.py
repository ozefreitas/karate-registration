from rest_framework import serializers
import registration.serializers
import core.serializers.categories
from django.utils.text import slugify
from .models import Event, Discipline, Announcement, DisciplineMember, DisciplineTeam
from datetime import date


class EventsSerializer(serializers.ModelSerializer):
    individuals = serializers.SerializerMethodField()
    is_open = serializers.SerializerMethodField()
    is_closed = serializers.SerializerMethodField()
    is_retification = serializers.SerializerMethodField()
    number_registrations = serializers.SerializerMethodField()
    has_any_team = serializers.SerializerMethodField()
    has_any_indiv = serializers.SerializerMethodField()
    has_coach = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = "__all__"

    def get_individuals(self, obj):
        """Filters the members in the individuals fields based on que requesting user"""
        user = self.context['request'].user
        if not user.is_authenticated:
            return []
        if user.role == 'free_club' or user.role == 'subed_club':
            qs = obj.individuals.filter(club=user)
        elif user.role == 'main_admin' or user.role == 'superuser':
            qs = obj.individuals.all()
        else:
            return []
        return registration.serializers.CompactPersonSerializer(qs, many=True).data
    
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
            if not discipline.is_coach:
                number += discipline.individuals.count()
        return number
    
    def get_has_any_team(self, obj):
        disciplines = Discipline.objects.filter(event=obj, is_team=True, is_coach=False)
        if disciplines.count() > 0:
            return True
        return False
    
    def get_has_any_indiv(self, obj):
        disciplines = Discipline.objects.filter(event=obj, is_team=False, is_coach=False)
        if disciplines.count() > 0:
            return True
        return False
    
    def get_has_coach(self, obj):
        disciplines = Discipline.objects.filter(event=obj, is_team=False, is_coach=True)
        if disciplines.count() > 0:
            return True
        return False


class CompactEventsSerializer(serializers.ModelSerializer):
    is_open = serializers.SerializerMethodField()
    is_closed = serializers.SerializerMethodField()
    is_retification = serializers.SerializerMethodField()
    number_registrations = serializers.SerializerMethodField()
    has_any_team = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = ["id", 
                  "name", 
                  "event_date", 
                  "season",
                  "location",
                  "has_registrations",
                  "has_ended",
                  "is_open", 
                  "is_closed", 
                  "is_retification", 
                  "number_registrations", 
                  "has_any_team", 
                  "encounter_type",
                  "description"]

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
            if not discipline.is_coach:
                number += discipline.individuals.count()
        return number

    def get_has_any_team(self, obj):
        disciplines = Discipline.objects.filter(event=obj)
        for discipline in disciplines:
            if discipline.is_team:
                return True
        return False


class CreateEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
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
        model = Event
        exclude = ("id", "has_ended")


class GenerateDrawResponseSerializer(serializers.Serializer):
    message = serializers.CharField()


class DisciplineDrawSerializer(serializers.Serializer):
    disciplineId = serializers.IntegerField()
    splitClubs = serializers.BooleanField()
    splitFavourites = serializers.BooleanField()
    format = serializers.CharField()
    maxMembersPerGroup = serializers.CharField(required=False, allow_blank=True)
    minMembersPerGroup = serializers.CharField(required=False, allow_blank=True)


class GenerateDrawRequestSerializer(serializers.Serializer):
    disciplines = DisciplineDrawSerializer(many=True)
    notificate = serializers.BooleanField()


class DisciplinesSerializer(serializers.ModelSerializer):
    individuals = serializers.SerializerMethodField()
    teams = serializers.SerializerMethodField()
    categories = core.serializers.categories.CategorySerializer(many=True)
    
    class Meta:
        model = Discipline
        fields = "__all__"

    def get_individuals(self, obj):
        user = self.context['request'].user
        event = self.context['request'].query_params.get("event_disciplines")

        if not user.is_authenticated:
            return []

        # Start with through model queryset
        qs = DisciplineMember.objects.filter(discipline=obj)

        if user.role in ['free_club', 'subed_club']:
            qs = qs.filter(person__club=user)
        elif user.role not in ['main_admin', 'superuser']:
            return []

        qs = qs.order_by('person__club__username')

        return DisciplineMemberSerializer(
            qs,
            many=True,
            context={
                **self.context,
                'discipline_categories': list(obj.categories.all()),
                'event_id': event,
                'restricted': self.context['request'].query_params.get("restricted")
            }
        ).data
    
    def get_teams(self, obj):
        user = self.context['request'].user
        event = self.context['request'].query_params.get("event_disciplines")

        if not user.is_authenticated:
            return []

        # Start with through model queryset
        qs = DisciplineTeam.objects.filter(discipline=obj)

        if user.role in ['free_club', 'subed_club']:
            qs = qs.filter(team__club=user)
        elif user.role not in ['main_admin', 'superuser']:
            return []

        qs = qs.order_by('team__club__username')

        return DisciplineTeamSerializer(
            qs,
            many=True,
            context={
                **self.context,
                'discipline_categories': list(obj.categories.all()),
                'event_id': event,
                'restricted': self.context['request'].query_params.get("restricted")
            }
        ).data


class DisciplineMemberSerializer(serializers.ModelSerializer):
    person = registration.serializers.CompactCategorizedPersonsSerializer()
    category = core.serializers.categories.NameCategorySerializer()

    class Meta:
        model = DisciplineMember
        fields = ["person", "added_at", "category"]


class DisciplineTeamSerializer(serializers.ModelSerializer):
    team = registration.serializers.TeamsSerializer()

    class Meta:
        model = DisciplineTeam
        fields = ["team", "added_at"]


class DisciplinesCompactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discipline
        fields = ["id", "name"]


class CreateDisciplineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discipline
        exclude = ["individuals", "teams", ]


class UpdateDisciplineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discipline
        exclude = ["id", ]


class AddMemberSerializer(serializers.Serializer):
    member_id = serializers.CharField()


class AddDisciplineMemberSerializer(serializers.Serializer):
    member_id = serializers.CharField()
    event_id = serializers.CharField()
    chosen_category = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True
    )


class DeleteMemberSerializer(serializers.Serializer):
    member_id = serializers.CharField()


class AddCategorySerializer(serializers.Serializer):
    category_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="Lista de IDs dos Escalões a adicionar à modalidade"
    )


class RemoveCategorySerializer(serializers.Serializer):
    category_id = serializers.CharField()


class DeleteTeamSerializer(serializers.Serializer):
    team_id = serializers.CharField()


class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = "__all__"