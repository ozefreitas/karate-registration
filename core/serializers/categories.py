from rest_framework import serializers
from core.models import Category

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
        fields = ("id", "name", "gender", "min_age", "max_age", "min_grad", "max_grad", "min_weight", "max_weight")


class CreateCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"

