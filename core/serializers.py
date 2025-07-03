from rest_framework import serializers
import dojos.models as models

class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        fields = ["id", "username", "role"]


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        exclude = ["password", ]