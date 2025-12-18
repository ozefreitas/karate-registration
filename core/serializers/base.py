from rest_framework import serializers
from core.models import User, SignupToken, RequestedAcount, RequestPasswordReset, Notification, MonthlyPaymentPlan
from events.serializers import CompactEventsSerializer


class CompactUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class MonthlyPaymentPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthlyPaymentPlan
        fields = "__all__"


class CreateMonthlyPaymentPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthlyPaymentPlan
        exclude = ["club_user"]


class RequestedAcountSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestedAcount
        fields = "__all__"


class GenerateTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = SignupToken
        fields = ["username", "alive_time"]


class TokenSerializer(serializers.Serializer):
    token = serializers.UUIDField()


class UsernameSerializer(serializers.Serializer):
    username = serializers.CharField()


class RegisterUserSerializer(serializers.ModelSerializer):
    """Will check for the tohen authenticity, expiration and usage before creating an user acount"""
    token = serializers.UUIDField()
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "username", "password", "token"]

    def validate(self, data):
        try:
            token = SignupToken.objects.get(token=data['token'], is_used=False)
        except SignupToken.DoesNotExist:
            raise serializers.ValidationError("Invalid or used token.")

        if token.is_expired():
            raise serializers.ValidationError("Token has expired.")

        data['username'] = token.username
        data['token_obj'] = token
        return data
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name'),
            email=validated_data.get('email'),
            password=validated_data['password']
        )
        validated_data['token_obj'].is_used = True
        validated_data['token_obj'].save()
        return user


class PasswordRequestsSerializer(serializers.ModelSerializer):
    club_user = CompactUserSerializer()

    class Meta:
        model = RequestPasswordReset
        fields = "__all__"


class RequestPasswordResetSerializer(serializers.Serializer):
     username_or_email = serializers.CharField(write_only=True)


class PasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ["password", ]


class NotificationsSerializer(serializers.ModelSerializer):
    target_event = CompactEventsSerializer()
    class Meta:
        model = Notification
        fields = "__all__"

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["club_user"].queryset = User.objects.filter(role__in=["free_club", "subed_club"])


class CreateNotificationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        exclude = ["request_acount"]


class AllUsersNotificationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        exclude = ["club_user"]