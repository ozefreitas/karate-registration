from rest_framework import serializers
import dojos.models as models
import registration.serializers 


class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        fields = ["id", "username", "role"]


class EventsSerializer(serializers.ModelSerializer):
    individuals = serializers.SerializerMethodField()
    # individuals = registration.serializers.CompactAthletesSerializer(many=True)
    teams = registration.serializers.TeamsSerializer(many=True)
    
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
        elif user.role == 'national_association' or user.role == 'superuser':
            qs = obj.individuals.all()
        else:
            return []
        return registration.serializers.CompactAthletesSerializer(qs, many=True).data


class CreateEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Event
        exclude = ("id", "has_ended", "individuals", "teams", "rating", )


class UpdateEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Event
        exclude = ("id", "has_ended")


class NotificationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Notification
        fields = "__all__"

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["dojo"].queryset = models.User.objects.filter(role__in=["free_dojo", "subed_dojo"])


class AddAthleteSerializer(serializers.Serializer):
    athlete_id = serializers.CharField()


class AddTeamSerializer(serializers.Serializer):
    team_id = serializers.CharField()


class RatingSerializer(serializers.Serializer):
    rating_signal = serializers.IntegerField()


class RegisterUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        fields = ["first_name", "last_name", "email", "username", "password"]
    
    def create(self, validated_data):
        user = models.User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            password=validated_data['password']
        )
        return user