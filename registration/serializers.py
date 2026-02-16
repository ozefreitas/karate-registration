from rest_framework import serializers
from decouple import config
from django.utils import timezone

import registration.models as models
from core.serializers.users import UsersSerializer
from core.serializers.categories import NameCategorySerializer
from core.models import MemberValidationRequest, MonthlyPaymentPlan
from core.utils.utils import calc_age
from events.models import Event, Discipline
from registration.utils.utils import get_comp_age
from registration.utils.utils import get_real_member, get_identity_members


### Members Serializer Classes

class MembersSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    request_status = serializers.SerializerMethodField()
    exam_request_status = serializers.SerializerMethodField()
    updated_by = UsersSerializer()
    current_month_payment_status = serializers.SerializerMethodField()
    past_month_payment_status = serializers.SerializerMethodField()

    class Meta:
        model = models.Member
        fields = ("id", 
                  "full_name", 
                  "gender",
                  "updated_by", 
                  "age", 
                  "member_type", 
                  "current_month_payment_status", 
                  "past_month_payment_status", 
                  "request_status",
                  "exam_request_status",
                  "is_validated",
                  "weight")


    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_age(self, obj):
        return get_comp_age(obj.birth_date)
    
    def get_request_status(self, obj):
        try:
            real = get_real_member(obj)
            ola = real.validation_requests.filter(request_type="verify")
            for coczinhos in ola:
                if coczinhos.status == "approved":
                    return "approved"
                elif coczinhos.status == "pending":
                    return "pending"
                else:
                    return "rejected"
        except MemberValidationRequest.DoesNotExist:
            return None

    def get_exam_request_status(self, obj):
        try:
            real = get_real_member(obj)
            ola = real.validation_requests.filter(request_type="exams")
            for coczinhos in ola:
                if coczinhos.status == "approved":
                    return "approved"
                elif coczinhos.status == "pending":
                    return "pending"
                else:
                    return "rejected"
        except MemberValidationRequest.DoesNotExist:
            return None
    
    def get_current_month_payment_status(self, obj):
        return obj.current_month_payment()
    
    def get_past_month_payment_status(self, obj):
        return obj.past_month_payment()


class AdminMembersSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    club = UsersSerializer()
    updated_by = UsersSerializer()

    class Meta:
        model = models.Member
        fields = ("id", 
                  "full_name", 
                  "gender", 
                  "club", 
                  "updated_by")


    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class CompactMembersSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    club = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()

    class Meta:
        model = models.Member
        fields = ["id", "gender", "club", "full_name", "age", "weight"]

    def get_club(self, obj):
        return obj.club.username
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    
    def get_age(self, obj):
        return get_comp_age(obj.birth_date)


class CompactCategorizedMembersSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    # category = serializers.SerializerMethodField()
    club = serializers.SerializerMethodField()

    class Meta:
        model = models.Member
        fields = ["id", "first_name", "last_name", "gender", "club", "full_name"]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        drop = self.context.get("restricted", [])

        if drop == "true":
            self.fields.pop("id", None)

    def get_club(self, obj):
        return obj.club.username
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    
    # def get_category(self, obj):
    #     """Sends the category of each member if a category is provided. 
    #     Categories comming from the context are only the ones linked to the respective Discipline"""
        
    #     categories = self.context.get('discipline_categories', [])
    #     if categories == []:
    #         return None
        
    #     event_id = self.context['request'].query_params.get("event_disciplines")
    #     try:
    #         event = Event.objects.get(id=event_id)
    #         season = event.season.split("/")[0]
    #     except Event.DoesNotExist:
    #         raise serializers.ValidationError("Event does not exist.")
        
    #     current_age = get_comp_age(obj.birth_date)
        
    #     if current_age <= 0 or current_age is None:
    #         return None
        
    #     age_method = config('AGE_CALC_REF')
    #     event_age = current_age if age_method == "true" else calc_age(age_method, obj.birth_date, season)
    #     for category in categories:
    #         if category.gender == obj.gender:
    #             if category.min_age <= event_age <= category.max_age:

    #                 if obj.weight is not None:
    #                     if category.min_weight is not None and category.max_weight is not None:
    #                         if category.min_weight <= obj.weight <= category.max_weight:
    #                             return f'{category.name} +{category.max_weight}'
    #                         else:
    #                             continue
    #                     if category.max_weight is not None:
    #                         if obj.weight < category.max_weight:
    #                             return f'{category.name} -{category.max_weight}'
    #                     elif category.min_weight is not None:
    #                         if obj.weight >= category.min_weight:
    #                             return f'{category.name} +{category.min_weight}'
    #                     else:
    #                         return category.name
    #                 else:
    #                     return category.name
    #     return None


class NotAdminLikeTypeMembersSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    monthly_payment_status = serializers.SerializerMethodField()
    monthly_payment_config = serializers.SerializerMethodField()
    has_another = serializers.SerializerMethodField()
    next_prev = serializers.SerializerMethodField()
    
    class Meta:
        model = models.Member
        exclude = ("creation_date", "created_by", "club", "favorite")

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_age(self, obj):
        return get_comp_age(obj.birth_date)
    
    def get_monthly_payment_status(self, obj):
        return obj.current_month_payment()

    def get_monthly_payment_config(self, obj):
        # Get or create the payment plan row
        default_plan, _ = MonthlyPaymentPlan.objects.get_or_create(
                club_user=obj.club,
                is_default=True,
                defaults={"name": "Default", "amount": 10}
            )
        # Get or create config row

        config, _ = models.MonthlyMemberPaymentConfig.objects.get_or_create(
            member=get_real_member(obj),
            defaults={"base_plan": default_plan}
        )

        return MonthlyMemberPaymentConfigSerializer(config).data
    
    def get_has_another(self, obj):
        if get_identity_members(obj, True).exists():
            return get_identity_members(obj, True).first().id
        else: return None

    def get_next_prev(self, obj):
        qs = list(
            models.Member.objects
            .filter(club=obj.club)
            .order_by("first_name", "last_name", "id")
            .values_list("id", flat=True)
        )

        try:
            index = qs.index(obj.id)
        except ValueError:
            return [{"prev": None, "next": None}]

        prev_id = qs[index - 1] if index > 0 else None
        next_id = qs[index + 1] if index < len(qs) - 1 else None

        return {
            "prev": next_id,
            "next": prev_id,
        }


class AdminLikeTypeMembersSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()

    class Meta:
        model = models.Member
        exclude = ("quotes_legible", "creation_date", "favorite", "club", "created_by", "member_type")

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_age(self, obj):
        return get_comp_age(obj.birth_date)
    

class NotInEventCoachesSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = models.Member
        fields = ["id", "gender", "full_name", "graduation"]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class NotInEventMembersSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    
    class Meta:
        model = models.Member
        fields = ["id", "weight", "gender", "age", "full_name", "category"]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_age(self, obj):
        event_id = self.context['request'].query_params.get("not_in_event")

        try:
            event = Event.objects.get(id=event_id)
            season = event.season.split("/")[0]
        except Event.DoesNotExist:
            raise serializers.ValidationError("Event does not exist.")
        
        age_method = config('AGE_CALC_REF')
        current_age = get_comp_age(obj.birth_date)
        event_age = current_age if age_method == "true" else calc_age(age_method, obj.birth_date, season)
        return event_age
    
    def get_category(self, obj):
        """Sends the category of each member if a category is provided. 
        Categories comming from the context are only the ones linked to the respective Discipline"""
        
        discipline_id = self.context['request'].query_params.get("discipline_id", None)
        if discipline_id is None:
            return discipline_id
        
        try:
            discipline = Discipline.objects.get(id=discipline_id)
        except Discipline.DoesNotExist:
            raise serializers.ValidationError("Discipline does not exist.")

        categories = list(discipline.categories.all())
        if categories == []:
            return None
        
        event_id = self.context['request'].query_params.get("not_in_event")

        try:
            event = Event.objects.get(id=event_id)
            season = event.season.split("/")[0]
        except Event.DoesNotExist:
            raise serializers.ValidationError("Event does not exist.")
        
        current_age = get_comp_age(obj.birth_date)
        
        if current_age <= 0 or current_age is None:
            return None
        
        age_method = config('AGE_CALC_REF')
        event_age = current_age if age_method == "true" else calc_age(age_method, obj.birth_date, season)
        for category in categories:
            if category.min_age <= event_age <= category.max_age:
                return category.name
                
        return None
    

class UploadMemberProfilePictureSerializer(serializers.Serializer):
    profile_image = serializers.ImageField(required=False)

    class Meta:
        model = models.Member
        fields = "__all__"


class ClubsCreateMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Member
        fields = "__all__"
        read_only_fields = ("club", ) 

    def validate(self, data):
        weight = data.get("weight")
        stundent = data.get("student")
        gender = data.get("gender")
        birth_date = data.get("birth_date")
        member_type = data.get("member_type")

        if member_type in ["student", "athlete"] and models.Member.objects.filter(first_name=data.get("first_name"),
                                                                     last_name=data.get("last_name"),
                                                                     birth_date=birth_date,
                                                                     id_number=data.get("id_number"),
                                                                     member_type__in=["athlete", "student"]).exists():

            raise serializers.ValidationError({
                'member_type_missmatch': ['Já existe um "Aluno" para este Membro.']
            })
        
        elif member_type == "coach" and models.Member.objects.filter(first_name=data.get("first_name"),
                                                                     last_name=data.get("last_name"),
                                                                     birth_date=birth_date,
                                                                     id_number=data.get("id_number"),
                                                                     member_type="coach").exists():
            raise serializers.ValidationError({
                        'member_type_missmatch': ['Já existe um "Treinador" para este Membro.']
                    })
        
        current_age = get_comp_age(birth_date)
        if current_age <= 0:
            raise serializers.ValidationError({
                'impossible_age': [f"A data de nascimento não parece correta porque a idade resulta em {current_age} anos."]
            })

        if stundent and weight != "":
            raise serializers.ValidationError({
                'incompatible_member': ["Alunos não têm peso associado."]
            })
    
        if gender not in ["Masculino", "Feminino"]:
            raise serializers.ValidationError({
                'impossible_gender': ['Género "Misto" apenas está disponível para Equipas.']
            })
      
        return data
    

class AdminCreateMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Member
        exclude = ("address", "post_code", "national_card_number", "taxpayer_number")

    def validate(self, data):
        weight = data.get("weight")
        stundent = data.get("student")
        gender = data.get("gender")

        if stundent and weight != "":
            raise serializers.ValidationError({
                'incompatible_member': ["Alunos não têm peso associado."]
            })
    
        if gender not in ["Masculino", "Feminino"]:
            raise serializers.ValidationError({
                'impossible_gender': ['Género "Misto" apenas está disponível para Equipas.']
            })
      
        return data


class UpdateMemberSerializer(serializers.ModelSerializer):
    age = serializers.SerializerMethodField()

    def get_age(self, obj):
        return get_comp_age(obj.birth_date)
    
    class Meta:
        model = models.Member
        exclude = ("club", "created_by", "creation_date")
    
    def get_fields(self):
        fields = super().get_fields()

        member = self.instance
        request = self.context.get("request")

        if member and request:
            if member.created_by == member.club and member.created_by.role != "main_admin" and member.is_validated and request.user.role != "main_admin":
                for field in ["id_number", "first_name", "last_name", "birth_date", "gender", "graduation"]:
                    fields.pop(field, None)

        return fields

    def validate(self, attrs):
        member = self.instance 
        request = self.context.get("request")
        if request.user.role in ["main_admin", "superuser"]:
            return attrs

        if (member.created_by.role != "main_admin" and member.created_by != member.club) or (member.created_by.role != "main_admin" and member.created_by == member.club and member.is_validated):
            for field in ["id_number", "first_name", "last_name", "birth_date", "gender", "graduation"]:
                if field in attrs:
                    raise serializers.ValidationError(
                        {"not_allowed": "Não pode alterar campos sensíveis de um membro criado/verificado pelo seu administrador.", "field": field}
                    )

        return attrs


### Monthly Payments Serializer Classes

class MonthlyMemberPaymentConfigSerializer(serializers.ModelSerializer):
    base_plan_amount = serializers.SerializerMethodField()

    class Meta:
        model = models.MonthlyMemberPaymentConfig
        exclude = ("member", )

    def get_base_plan_amount(self, obj):
        return obj.base_plan.amount


class PatchMonthlyMemberPaymentConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MonthlyMemberPaymentConfig
        fields = "__all__"
        read_only_fields = ["member"]


class MonthlyMemberPaymentSerializer(serializers.ModelSerializer):
    inside_limit = serializers.SerializerMethodField()
    predefined_amount = serializers.SerializerMethodField()
    is_custom = serializers.SerializerMethodField()
    member = CompactMembersSerializer()

    class Meta:
        model = models.MonthlyMemberPayment
        fields = "__all__"
    
    def get_inside_limit(self, obj):
        if obj.paid == True:
            if obj.paid_at > obj.due_date:
                return False
            else: return True
        if obj.due_date != None:
            return timezone.now() < obj.due_date
        else: return True

    def get_predefined_amount(self, obj):
        pred_amount = models.MonthlyMemberPaymentConfig.objects.get(member=obj.member)
        if pred_amount.is_custom_active:
            return pred_amount.custom_amount
        else:
            return pred_amount.base_plan.amount
    
    def get_is_custom(self, obj):
        is_custom = models.MonthlyMemberPaymentConfig.objects.get(member=obj.member)
        return is_custom.is_custom_active


class CreateMonthlyMemberPaymentSerializer(serializers.ModelSerializer):
    amount = serializers.CharField(read_only=True)

    customAmount = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True
    )

    plan = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True
    )

    is_default = serializers.BooleanField(
        required=False,
        write_only=True
    )

    class Meta:
        model = models.MonthlyMemberPayment
        exclude = ["due_date", "paid", "paid_at"]

    def validate(self, attrs):
        if attrs.get("customAmount") and attrs.get("is_default"):
            raise serializers.ValidationError(
                "customAmount and is_default cannot be provided at the same time."
            )
        return attrs
    
    def create(self, validated_data):
        custom_amount = validated_data.pop("customAmount", None)
        is_default = validated_data.pop("is_default", False)
        plan = validated_data.pop("plan", None)
        old_member = validated_data.pop("member", False)

        request = self.context["request"]

        if is_default:
            default_plan = MonthlyPaymentPlan.objects.get(
                club_user=request.user,
                is_default=True
            )
            amount = default_plan.amount
        elif plan != None:
            custom_plan = MonthlyPaymentPlan.objects.get(id=plan)
            amount = custom_plan.amount
        else:
            amount = custom_amount or 0

        cannonical = get_real_member(old_member)

        return models.MonthlyMemberPayment.objects.create(
            **validated_data,
            member=cannonical,
            amount=amount
        )


class PatchMonthlyMemberPaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.MonthlyMemberPayment
        fields = ["paid", "amount"]

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


class MembersPaymentsStatusSerializer(serializers.Serializer):
    number = serializers.IntegerField()
    unpaid_members = serializers.IntegerField()


### Teams Serializer Classes

class TeamsSerializer(serializers.ModelSerializer):
    athlete1 = CompactMembersSerializer()
    athlete2 = CompactMembersSerializer()
    athlete3 = CompactMembersSerializer()
    athlete4 = CompactMembersSerializer()
    athlete5 = CompactMembersSerializer()
    team_size = serializers.SerializerMethodField()
    category = NameCategorySerializer()
    disciplines = serializers.SerializerMethodField()
    events = serializers.SerializerMethodField()

    class Meta:
        model = models.Team
        exclude = ["creation_date", "modified_date", "club"]
    
    def get_team_size(self, obj):
        members = [obj.athlete1, obj.athlete2, obj.athlete3, obj.athlete4, obj.athlete5]
        return sum(1 for member in members if member is not None)
    
    def get_disciplines(self, obj):
        return obj.disciplines_team.values_list("name", flat=True)
    
    def get_events(self, obj):
        return obj.disciplines_team.values_list("event__name", flat=True).distinct()


class CreateTeamSerializer(serializers.ModelSerializer):
    chosen_category = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True
    )
    
    class Meta:
        model = models.Team
        exclude = ("club", "team_number", "category")
    
    def validate(self, data):
        athletes = [
            data.get("athlete1"),
            data.get("athlete2"),
            data.get("athlete3"),
            data.get("athlete4"),
            data.get("athlete5"),
        ]

        athletes = [a for a in athletes if a is not None]

        if len(athletes) != len(set(athletes)):
            raise serializers.ValidationError({
                "athletes": "Uma Equipa não pode ter Membros repetidos."
            })

        return data
    

class UpdateTeamsSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = models.Team
        exclude = ("club", "team_number", "gender")


### Classifications Serializer Classes

class AllClassificationsSerializer(serializers.ModelSerializer):
    competition = serializers.SerializerMethodField()
    full_category = serializers.SerializerMethodField()
    first_place = serializers.SerializerMethodField()
    second_place = serializers.SerializerMethodField()
    third_place = serializers.SerializerMethodField()

    def format_member_name(self, name: str) -> str:
        return name.lower().capitalize()

    class Meta:
        model = models.Classification
        fields = "__all__"

    def get_full_category(self, obj):
        return f"{obj.first_place.match_type.capitalize()} {obj.first_place.category} {obj.first_place.gender.capitalize()}"
    
    def get_competition(self, obj):
        return f"{obj.competition.name} {obj.competition.season}"
    
    def get_first_place(self, obj):
        return f"{self.format_member_name(obj.first_place.first_name)} {self.format_member_name(obj.first_place.last_name)}"
    
    def get_second_place(self, obj):
        return f"{self.format_member_name(obj.second_place.first_name)} {self.format_member_name(obj.second_place.last_name)}"
    
    def get_third_place(self, obj):
        return f"{self.format_member_name(obj.third_place.first_name)} {self.format_member_name(obj.third_place.last_name)}"
    

class ClassificationsSerializer(serializers.ModelSerializer):
    full_category = serializers.SerializerMethodField()
    first_place = CompactMembersSerializer()
    second_place = CompactMembersSerializer()
    third_place = CompactMembersSerializer()

    class Meta:
        model = models.Classification
        exclude = ("competition", )

    def get_full_category(self, obj):
        return f"{obj.first_place.match_type.capitalize()} {obj.first_place.category} {obj.first_place.gender.capitalize()}"


class CreateClassificationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Classification
        fields = "__all__"