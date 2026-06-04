from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction, IntegrityError
from django.utils import timezone
from django.db.models import Case, When

from .models import Team, Classification, MonthlyPersonPayment, MonthlyPersonPaymentConfig, Person, Membership
from .filters import PersonsFilters, MonthlyPersonPaymentFilters, ClassificationsFilters
from events.models import Event
from core.models import User, Notification, MonthlyPaymentPlan
from core.permissions import PersonPermission
import registration.serializers.serializers as registration_serializers
import events.serializers as event_serializers

from datetime import datetime

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from drf_spectacular.utils import extend_schema

# views for the athlets registrations

class MultipleSerializersMixIn:
    serializer_classes = {}

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, self.serializer_class)
    
    def get_serializer(self, *args, **kwargs):
        return super().get_serializer(*args, **kwargs)


class PersonsViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    queryset=queryset = Person.objects.prefetch_related("member_types").order_by("first_name", "last_name", "id")
    serializer_class = registration_serializers.PersonsSerializer  
    permission_classes = [PersonPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ["first_name", "last_name", "gender", "birth_date"]
    filterset_class = PersonsFilters
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    serializer_classes = {
        "create": registration_serializers.ClubsCreatePersonSerializer,
        "retrieve": registration_serializers.NotAdminLikeTypePersonsSerializer,
        "update": registration_serializers.UpdatePersonSerializer,
        "partial_update": registration_serializers.UpdatePersonSerializer
    }

    @extend_schema(responses=registration_serializers.NotAdminLikeTypePersonsSerializer)
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(request=registration_serializers.ClubsCreatePersonSerializer)
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(responses=registration_serializers.UpdatePersonSerializer)
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset.none()

        user = self.request.user

        # safety guard
        if not user.is_authenticated:
            return self.queryset.none()

        role = getattr(user, "role", None)

        if role == "superuser":
            return self.queryset

        if role in ["main_admin", "single_admin"]:
            return self.queryset.filter(
                is_validated=True,
                member_types__member_type__in=["athlete", "student"]
            ).exclude(
                club__role__in=["superuser"]
            )

        if role in ["subed_club", "free_club"]:
            return self.queryset.filter(club=user)

        raise PermissionDenied("You do not have access to this data.")

    def get_serializer_class(self):
        if getattr(self, "swagger_fake_view", False):
            return registration_serializers.PersonsSerializer

        user = self.request.user
        role = getattr(user, "role", None)

        if self.action == "list":
            if role in ["free_club", "subed_club"]:
                if self.request.query_params.get("not_in_event"):
                    return registration_serializers.NotInEventPersonsSerializer
                elif self.request.query_params.get("coach_not_in_event"):
                    return registration_serializers.NotInEventCoachesSerializer
                else:
                    return registration_serializers.PersonsSerializer
            else:
                return registration_serializers.AdminPersonsSerializer

        if self.action == "retrieve":
            if role in ["free_club", "subed_club"]:
                return registration_serializers.NotAdminLikeTypePersonsSerializer
            return registration_serializers.AdminPersonRetrieveSerializer

        elif self.action == "create":
            if role in ["free_club", "subed_club"]:
                return registration_serializers.ClubsCreatePersonSerializer
            return registration_serializers.AdminCreatePersonSerializer

        return super().get_serializer_class()

    @extend_schema(request=registration_serializers.ClubsCreatePersonSerializer)
    def perform_create(self, serializer):
        request_user = self.request.user
        id_number = serializer.validated_data.get("id_number")
        first_name = serializer.validated_data.get("first_name")
        last_name = serializer.validated_data.get("last_name")
        member_types = serializer.validated_data.pop("member_type", None) 

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
            person = serializer.save(id_number=id_number, created_by=request_user)
            Membership.objects.create(member_type="student", person=person)
        elif request_user.role == "subed_club":
            user = request_user
            person = serializer.save(id_number=id_number, club=user, created_by=request_user)
            for member_type in member_types:
                Membership.objects.create(member_type=member_type, person=person)

        try:
            with transaction.atomic():
                default_plan, _ = MonthlyPaymentPlan.objects.get_or_create(
                    club_user=user,
                    is_default=True,
                    defaults={"name": "Default", "amount": 10}
                )
        except IntegrityError:
            default_plan = MonthlyPaymentPlan.objects.get(
                club_user=user,
                is_default=True
            )

        person_base_plan, _ = MonthlyPersonPaymentConfig.objects.get_or_create(
            person=person,
            defaults={"base_plan": default_plan}
        )

        final_amount = None
        if not person_base_plan.is_custom_active:
            final_amount = person_base_plan.base_plan.amount
        else:
            final_amount=person_base_plan.custom_amount

        today = datetime.today()
        MonthlyPersonPayment.objects.get_or_create(
            person=person,
            year=today.year,
            month=today.month,
            defaults={"amount": final_amount}
        )

    @extend_schema(responses=registration_serializers.UpdatePersonSerializer)
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
        updated_person = serializer.save(updated_by=request.user, is_validated=instance.is_validated)

        if request.user != instance.club:
            Notification.objects.create(type="member_updated",
                                        notification=f'O Membro {old_identity["first_name"]} {old_identity["last_name"]} foi atualizado pelo seu administrador.',
                                        target_person=updated_person,
                                        can_remove=True,
                                        club_user=instance.club,
                                        )

        if request.user.role == "main_admin":
            identity_fields = ["first_name", "last_name", "birth_date", "id_number"]
        else:
            identity_fields = ["gender", "weight", "taxpayer_number", "national_card_number", "address"]
        new_identity = {field: getattr(updated_person, field) for field in identity_fields}

        #  others.update(**new_identity, updated_by=request.user)

        return Response(
            {
                "data": self.get_serializer(updated_person).data,
                "message": "Membro atualizado com sucesso!",
            },
            status=status.HTTP_200_OK
        )

    @extend_schema(
        responses=registration_serializers.PersonsSerializer(many=True),
    )
    @action(detail=False, methods=["get"], url_path="last_five", pagination_class=None)
    def last_five(self, request):
        last_five = Person.objects.filter(club=request.user).order_by('-modified_date')[:5]
        serializer = registration_serializers.PersonsSerializer(last_five, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['delete'], url_path="delete_all")
    def delete_all(self, request):
        deleted_count, _ = Person.objects.filter(club=request.user).delete()
        if deleted_count <= 1:
            return Response(
                {"message": "Membro eliminado."},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"message": f"Eliminados {deleted_count} Membros."},
                status=status.HTTP_200_OK
            )
    
    @extend_schema(
        responses=registration_serializers.PersonsPaymentsStatusSerializer
    )
    @action(detail=False, methods=['get'], url_path="members_payments_status")
    def members_payments_status(self, request):
        paying_members = Person.objects.filter(
            club=request.user,
            quotes_legible=True
        ).values(
            "first_name",
            "last_name",
            "birth_date",
            "id_number"
        ).distinct().count()

        today = timezone.now()

        if today.month == 1:
            prev_month = 12
            prev_year = today.year - 1
        else:
            prev_month = today.month - 1
            prev_year = today.year

        unpaid_members = Person.objects.filter(
            club=request.user,
            payments__year=prev_year,
            payments__month=prev_month,
            payments__paid=False
        ).values(
            "first_name",
            "last_name",
            "birth_date",
            "id_number"
        ).distinct().count()

        return Response(
            {"number": paying_members, "unpaid_members": unpaid_members},
            status=status.HTTP_200_OK
        )
    
    @extend_schema(responses=event_serializers.DisciplinesCompactSerializer(many=True))
    @action(detail=True, methods=['get'], url_path='unregistered_modalities/(?P<event_id>[^/.]+)')
    def unregistered_modalities(self, request, pk=None, event_id=None):
        try:
            person = self.get_object()
            event = Event.objects.get(pk=event_id)
        except Event.DoesNotExist:
            return Response({"detail": "Event not found."}, status=status.HTTP_404_NOT_FOUND)

        # All disciplines of the event
        event_disciplines = event.disciplines.filter(is_coach=False)

        # Modalities where the member is already registered
        registered = person.disciplines_indiv.filter(event=event)

        # Difference = unregistered
        unregistered = event_disciplines.exclude(id__in=registered.values_list('id', flat=True))

        serializer = event_serializers.DisciplinesCompactSerializer(unregistered, many=True)
        return Response(serializer.data)


class MemberShipsViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    # TODO: order get request by the category_index from the serializer
    queryset=Membership.objects.all().order_by("person__first_name", "person__last_name", "person__id")
    serializer_class = registration_serializers.MemberShipsSerializer
    permission_classes = [PersonPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]

    serializer_classes = {
        "create": registration_serializers.CreateMemberShipsSerializer,
        # "update": registration_serializers.UpdateMemberSerializer
    }

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset.none()
        
        user = self.request.user
        if not user.is_authenticated:
            return self.queryset.none()
        
        if user.role == "main_admin":
            raise PermissionDenied("You do not have access to this data.")
        
        else: return self.queryset
    

class MonthlyPersonPaymentViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    queryset=MonthlyPersonPayment.objects.all()
    serializer_class = registration_serializers.MonthlyPersonPaymentSerializer
    pagination_class = None
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ["year", "month", "paid_at", "paid"]
    permission_classes = [IsAuthenticated]
    filterset_class = MonthlyPersonPaymentFilters

    serializer_classes = {
        "create": registration_serializers.CreateMonthlyPersonPaymentSerializer,
        "partial_update": registration_serializers.PatchMonthlyPersonPaymentSerializer
    }

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return MonthlyPersonPayment.objects.none()
        return super().get_queryset().filter(person__club=user)
    

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


class MonthlyPersonPaymentConfigViewSet(viewsets.ModelViewSet):
    queryset = MonthlyPersonPaymentConfig.objects.all()
    serializer_class = registration_serializers.MonthlyPersonPaymentConfigSerializer
    permission_classes = [IsAuthenticated]


class TeamsViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    queryset=Team.objects.all()
    serializer_class = registration_serializers.TeamsSerializer
    permission_classes = [IsAuthenticated, PersonPermission]

    serializer_classes = {
        "create": registration_serializers.CreateTeamSerializer,
        "update": registration_serializers.UpdateTeamsSerializer
    }

    def get_queryset(self):
        return self.queryset.filter(club=self.request.user)

    def perform_create(self, serializer):
        # Auto-generate id_number if it wasn't provided
        last_team = Team.objects.filter(club=self.request.user).order_by("team_number").last()
        team_number = (last_team.team_number if last_team else 0) + 1
        serializer.save(club=self.request.user, team_number=team_number)

    @extend_schema(
        responses=registration_serializers.TeamsSerializer(many=True),
    )
    @action(detail=False, methods=["get"], url_path="last_five", pagination_class=None)
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
    queryset = Classification.objects.annotate(
        place_order=Case(
            When(place=2, then=0),
            When(place=1, then=1),
            When(place=3, then=2),
        )
    ).order_by("place_order")
    serializer_class = registration_serializers.ClassificationsSerializer
    filterset_class = ClassificationsFilters

    serializer_classes = {
        "create": registration_serializers.CreateClassificationsSerializer,
    }
    
    @action(detail=False, methods=["get"], url_path="last_comp_quali")
    def last_comp_quali(self, request):
        now = timezone.now()
        last_competition = Event.objects.filter(event_date__gte=now).order_by('event_date').last()
        if last_competition is None:
            return Response([])

        last_comp_quali = Classification.objects.filter(bracket__event=last_competition.id)
        serialized_data = registration_serializers.ClassificationsSerializer(last_comp_quali, many=True)

        # Group by bracket id
        grouped = {}
        for item in serialized_data.data:
            bracket_id = item["bracket"]["id"]
            if bracket_id not in grouped:
                grouped[bracket_id] = {
                    "bracket": item["bracket"],
                    "classifications": []
                }
            grouped[bracket_id]["classifications"].append({
                "person": item["person"],
                "place": item["place"],
                "created_at": item["created_at"]
            })

        return Response(list(grouped.values()))