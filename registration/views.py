from django_filters.rest_framework import DjangoFilterBackend

from .models import Member, Team, Classification, MonthlyMemberPayment, MonthlyMemberPaymentConfig
from .filters import MembersFilters, MonthlyMemberPaymentFilters
from events.models import Event
from core.models import User, Notification, MonthlyPaymentPlan
from core.permissions import MemberPermission
import registration.serializers as registration_serializers
import events.serializers as event_serializers
from registration.utils.utils import get_real_member, get_identity_members

from datetime import datetime

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied


# views for the athlets registrations

class MultipleSerializersMixIn:
    serializer_classes = {}

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, self.serializer_class)


class MembersViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    # TODO: order get request by the category_index from the serializer
    queryset=Member.objects.all().order_by("first_name")
    serializer_class = registration_serializers.MembersSerializer
    permission_classes = [MemberPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ["first_name", "last_name", "gender", "member_type", "birth_date"]
    filterset_class = MembersFilters

    serializer_classes = {
        "create": registration_serializers.ClubsCreateMemberSerializer,
        "update": registration_serializers.UpdateMemberSerializer
    }

    def get_queryset(self):
        user = self.request.user
        if user.role in ["main_admin", "superuser", "single_admin"]:
            # National-level user can see all Members
            return self.queryset.filter(created_by=user)

        if user.role in ["subed_club", "free_club"]:
            # paying clubs user sees only their own club Members
            return self.queryset.filter(club=user)
        
        raise PermissionDenied("You do not have access to this data.")

    def get_serializer_class(self):
        user = self.request.user
        if self.action == "retrieve":
            if user.role in ["free_club", "subed_club"]:
                return registration_serializers.NotAdminLikeTypeMembersSerializer
            return registration_serializers.AdminLikeTypeMembersSerializer

        elif self.action == "create":
            if user.role in ["free_club", "subed_club"]:
                return registration_serializers.ClubsCreateMemberSerializer
            return registration_serializers.AdminCreateMemberSerializer
        
        if self.request.query_params.get("not_in_event"):
            return registration_serializers.NotInEventMembersSerializer

        return super().get_serializer_class()
    
    def perform_create(self, serializer):
        request_user = self.request.user
        id_number = serializer.validated_data.get("id_number")
        first_name = serializer.validated_data.get("first_name")
        last_name = serializer.validated_data.get("last_name")

        if id_number == 0:
            # # Auto-generate id_number if it wasn't provided
            # last_Member = Member.objects.filter(id_number__isnull=False).order_by("id_number").last()
            # id_number = (last_Member.id_number if last_Member else 0) + 1
            id_number = None

        if request_user.role == "main_admin":
            club = serializer.validated_data.get('club')
            user = User.objects.get(username=club)
            Notification.objects.create(club_user=user, 
                                        notification=f"Um novo Membro ({first_name} {last_name}) acabou de ser criado. Verifique os seus dados e adicione outros campos caso necessário.",
                                        can_remove=True,
                                        type="create_member")
            member = serializer.save(id_number=id_number, created_by=request_user)
        elif request_user.role == "subed_club":
            user = request_user
            member = serializer.save(id_number=id_number, club=user, created_by=request_user)
        
        canonical = get_real_member(member)

        default_plan, _ = MonthlyPaymentPlan.objects.get_or_create(
                club_user=user,
                is_default=True,
                defaults={"name": "Default", "amount": 10}
            )

        member_base_plan, _ = MonthlyMemberPaymentConfig.objects.get_or_create(
            member=canonical,
            base_plan=default_plan
        )

        final_amount = None
        if not member_base_plan.is_custom_active:
            final_amount = member_base_plan.base_plan.amount
        else:
            final_amount=member_base_plan.custom_amount

        today = datetime.today()
        MonthlyMemberPayment.objects.get_or_create(
            member=canonical,
            year=today.year,
            month=today.month,
            defaults={"amount": final_amount}
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        old_identity = {
            "id": instance.id,
            "first_name": instance.first_name,
            "last_name": instance.last_name,
            "birth_date": instance.birth_date,
            "id_number": instance.id_number,
        }

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_member = serializer.save(updated_by=request.user)

        if request.user != instance.club:
            Notification.objects.create(type="member_updated",
                                        notification=f'O Membro {old_identity["first_name"]} {old_identity["last_name"]} foi atualizado pelo seu administrador.',
                                        target_member=updated_member,
                                        can_remove=True,
                                        club_user=instance.club,
                                        )

        others = get_identity_members(old_identity)

        keep_count = others.count()

        identity_fields = ["first_name", "last_name", "birth_date", "id_number"]
        new_identity = {field: getattr(updated_member, field) for field in identity_fields}

        if others.exists():
            others.update(**new_identity, updated_by=request.user)
            message = f"Membros (total de {keep_count + 1}) atualizados com sucesso!"
        else:
            message = "Membro atualizado com sucesso!"

        return Response(
            {
                "data": self.get_serializer(updated_member).data,
                "message": message,
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=["get"], url_path="last_five")
    def last_five(self, request):
        last_five = Member.objects.filter(club=request.user).order_by('-creation_date')[:5]
        serializer = registration_serializers.MembersSerializer(last_five, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['delete'], url_path="delete_all")
    def delete_all(self, request):
        deleted_count, _ = Member.objects.filter(club=request.user).delete()
        if deleted_count <= 1:
            return Response(
                {"message": "Atleta eliminado"},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"message": f"Eliminados {deleted_count} Membros"},
                status=status.HTTP_200_OK
            )
    
    @action(detail=True, methods=['get'], url_path='unregistered_modalities/(?P<event_id>[^/.]+)')
    def unregistered_modalities(self, request, pk=None, event_id=None):
        try:
            member = self.get_object()
            event = Event.objects.get(pk=event_id)
        except Event.DoesNotExist:
            return Response({"detail": "Event not found."}, status=status.HTTP_404_NOT_FOUND)

        # All modalities of the event
        event_disciplines = event.disciplines.all()

        # Modalities where the member is already registered
        registered = member.disciplines_indiv.filter(event=event)

        # Difference = unregistered
        unregistered = event_disciplines.exclude(id__in=registered.values_list('id', flat=True))

        serializer = event_serializers.DisciplinesCompactSerializer(unregistered, many=True)
        return Response(serializer.data)
    

class MonthlyMemberPaymentViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    queryset=MonthlyMemberPayment.objects.all()
    serializer_class = registration_serializers.MonthlyMemberPaymentSerializer
    pagination_class = None
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ["year", "month", "paid_at", "paid"]
    permission_classes = [IsAuthenticated]
    filterset_class = MonthlyMemberPaymentFilters

    serializer_classes = {
        # "create": serializers.CreateMemberSerializer,
        "partial_update": registration_serializers.PatchMonthlyMemberPaymentSerializer
    }

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return MonthlyMemberPayment.objects.none()
        return super().get_queryset().filter(member__club=user)
    

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()

        sent_fields = set(request.data.keys())

        serializer = self.get_serializer(
            instance, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)

        paid = serializer.validated_data.get("id_number")
        if paid and "amount" in sent_fields:
            raise PermissionDenied("You do not have permission to do this.")

        self.perform_update(serializer)

        # ---- Custom response logic ----
        response_data = serializer.data

        if "paid" in sent_fields:
            if instance.paid:
                response_data["message"] = "Quotas marcadas como Pago."
            else:
               response_data["message"] = "Quotas revertidas para Em Falta." 
        elif "amount" in sent_fields:
            response_data["message"] = "Montante atualizado."

        return Response(response_data)


class MonthlyMemberPaymentConfigViewSet(viewsets.ModelViewSet):
    queryset = MonthlyMemberPaymentConfig.objects.all()
    serializer_class = registration_serializers.MonthlyMemberPaymentConfigSerializer
    permission_classes = [IsAuthenticated]


class TeamsViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    queryset=Team.objects.all()
    serializer_class = registration_serializers.TeamsSerializer
    # authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated, MemberPermission]

    serializer_classes = {
        # "create": registration_serializers.CreateMemberSerializer,
        "update": registration_serializers.UpdateTeamsSerializer
    }

    def get_queryset(self):
        return self.queryset.filter(club=self.request.user)

    @action(detail=False, methods=["get"], url_path="last_five")
    def last_five(self, request):
        last_five = Team.objects.filter(club=request.user).order_by('creation_date')[:5]
        serializer = registration_serializers.TeamsSerializer(last_five, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['delete'], url_path="delete_all")
    def delete_all(self, request):
        deleted_count, _ = Team.objects.filter(club=request.user).delete()
        if deleted_count <= 1:
            return Response(
                {"message": "Equipa eliminada"},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"message": f"Eliminadas {deleted_count} Equipas"},
                status=status.HTTP_200_OK
            )


class ClassificationsViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    queryset=Classification.objects.all()
    serializer_class = registration_serializers.AllClassificationsSerializer
    # permission_classes = [IsAuthenticated]

    serializer_classes = {
        "create": registration_serializers.CreateClassificationsSerializer,
    }

    @action(detail=False, methods=["get"], url_path="per_comp")
    def per_comp(self, request):
        queryset = Classification.objects.all()
        serialized_data = registration_serializers.AllClassificationsSerializer(queryset, many=True)
        final_classification = {}
        competition = ""
        for classification in serialized_data.data:
            comp_dict = {}
            if competition == "" and classification["competition"] == competition:
                comp_dict[classification['full_category']] = {"first_place": classification["first_place"], 
                                                           "second_place": classification["second_place"],
                                                           "third_place": classification["third_place"]}
            else:
                competition = classification["competition"]
                comp_dict[classification['full_category']] = {"first_place": classification["first_place"], 
                                                           "second_place": classification["second_place"],
                                                           "third_place": classification["third_place"]}
            if competition not in final_classification.keys():
                final_classification[competition] = [comp_dict]
            else:
                final_classification[competition].append(comp_dict)

        if final_classification == {}:
            return Response([])
        
        return Response([final_classification])
    
    @action(detail=False, methods=["get"], url_path="last_comp_quali")
    def last_comp_quali(self, request):
        last_competition = Event.objects.filter(has_ended=True).order_by('event_date').last()
        if last_competition is None:
            return Response([])
        last_comp_quali = Classification.objects.filter(competition=last_competition.id)
        serialized_data = registration_serializers.ClassificationsSerializer(last_comp_quali, many=True)
        return Response(serialized_data.data)