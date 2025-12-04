from rest_framework import serializers
from .models import Club, ClubSubscription, ClubSubscriptionConfig
from core.serializers.users import UsersSerializer


class RatingSerializer(serializers.Serializer):
    rating_signal = serializers.IntegerField()


class ClubsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Club
        fields = "__all__"


class CreateClubSerializer(serializers.ModelSerializer):
    class Meta:
        model = Club
        exclude = ["is_registered", "mother_acount"]


class ClubSubscriptionsSerializer(serializers.ModelSerializer):
    club = UsersSerializer()
    class Meta:
        model = ClubSubscription
        fields = "__all__"


class CreateClubSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClubSubscription
        exclude = ["paid", "paid_at"]


class UpdateClubSubscriptionAmountSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClubSubscriptionConfig
        fields = ["amount"]


class PatchClubSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClubSubscription
        fields = ["paid"]

    def update(self, instance, validated_data):
        # If PATCH includes "paid": true → use your method
        if validated_data.get("paid") is True and instance.paid is False:
            instance.mark_as_paid()
            validated_data.pop("paid", None)  # remove so DRF doesn't overwrite
        
        elif validated_data.get("paid") is False and instance.paid is True:
            instance.paid = False
            instance.paid_at = None
            validated_data.pop("paid", None)

        # For other fields (normally you wouldn’t allow them anyway)
        return super().update(instance, validated_data)


class CreateAllClubsSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClubSubscription
        exclude = ["paid", "paid_at", "club"]