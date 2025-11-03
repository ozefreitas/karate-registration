from rest_framework import serializers
from core.models import User


class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "role", "tier"]