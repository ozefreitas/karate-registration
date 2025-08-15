from rest_framework import serializers
import dojos.models as models
from .models import Category, User, SignupToken, RequestedAcount

class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "role", "tier"]


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


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ["password", ]


class CategorySerializer(serializers.ModelSerializer):
    has_age = serializers.SerializerMethodField()
    has_grad = serializers.SerializerMethodField()
    has_weight = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ("id", "name", "gender", "min_age", "max_age", "min_grad", "max_grad", "min_weight", "max_weight", "has_age", "has_grad", "has_weight")
    
    def get_has_age(self, obj):
        if obj.min_age is not None or obj.max_age is not None:
            return "Sim"
        return "Não"
    
    def get_has_grad(self, obj):
        if obj.min_grad is not None or obj.max_grad is not None:
            return "Sim"
        return "Não"
    
    def get_has_weight(self, obj):
        if obj.min_weight is not None or obj.max_weight is not None:
            return "Sim"
        return "Não"


class CompactCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ("name", "gender", "min_age", "max_age", "min_grad", "max_grad", "min_weight", "max_weight")


class CreateCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"