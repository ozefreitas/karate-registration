from django.db.models import Q, Count, Case, When, IntegerField
from django.contrib.auth import get_user_model
from datetime import datetime
from django.utils import timezone

from .models import Club, ClubSubscription, ClubSubscriptionConfig
from core.models import Notification
import clubs.serializers as ClubSerializers
from core.permissions import IsGETforClubs, IsAdminRoleorHigher
from core.views import MultipleSerializersMixIn

from rest_framework import viewsets, filters, status
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.decorators import api_view, action
from drf_spectacular.utils import extend_schema

from datetime import date

# Create your views here.

User = get_user_model()

class ClubsViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    queryset=Club.objects.all()
    serializer_class=ClubSerializers.ClubsSerializer
    permission_classes = [IsGETforClubs]

    serializer_classes = {
        "create": ClubSerializers.CreateClubSerializer,
    }

    def perform_create(self, serializer):
        user = self.request.user
        if user.role != "main_admin":
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer.save(mother_acount=user)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminRoleorHigher])
def club_members(request):
    data = User.objects.exclude(role__in=["main_admin", "superuser", "technician"])\
                        .annotate(member_count=Count('member'),
                                    student_count=Count(
                                        Case(
                                            When(member__member_type='student', then=1),
                                            output_field=IntegerField(),
                                        )
                                    ),
                                    coach_count=Count(
                                        Case(
                                            When(member__member_type='coach', then=1),
                                            output_field=IntegerField(),
                                        )
                                    ),
                                    athlete_count=Count(
                                        Case(
                                            When(member__member_type='athlete', then=1),
                                            output_field=IntegerField(),
                                        )
                                    ),
                                ).values('username', 'member_count', 'student_count', 'coach_count', 'athlete_count')
    return Response(data)


class ClubSubscriptionsViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    queryset=ClubSubscription.objects.all().order_by("club")
    serializer_class=ClubSerializers.ClubSubscriptionsSerializer
    permission_classes = [IsAdminRoleorHigher]
    filter_backends = [filters.SearchFilter]
    search_fields = ['year']
    pagination_class = None
    serializer_classes = {
        "create": ClubSerializers.CreateClubSubscriptionSerializer,
        "partial_update": ClubSerializers.PatchClubSubscriptionSerializer
    }

    @action(detail=False, methods=['get'], url_path="get_available_quote_years")
    def get_available_quote_years(self, request):
        user = request.user
        if user.role not in ["main_admin", "superuser"]:
            return Response(
                {"error": "Não tem autorização para realizar esta ação"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        years = ClubSubscription.objects.values_list("year", flat=True).distinct().order_by("year")
        return Response({"years": years})
    

    @action(
        detail=False,
        methods=['patch'],
        url_path="update_subscription_amount",
        serializer_class=ClubSerializers.UpdateClubSubscriptionConfigAmountSerializer,
        permission_classes=[]
    )
    def update_subscription_amount(self, request):
        user = request.user
        
        if user.role not in ["main_admin", "superuser"]:
            return Response(
                {"error": "Não tem autorização para realizar esta ação"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data["amount"]

        config, _ = ClubSubscriptionConfig.objects.get_or_create(admin=user)

        config.amount = amount
        config.save()

        return Response(
            {
                "message": "Valor atualizado com sucesso",
                "admin": user.username,
                "amount": str(config.amount)
            },
            status=status.HTTP_200_OK
        )
    
    @extend_schema(description="An endpoint that targets all children accounts of an admin, in order to, update all subscription object if the given year," \
    "with a new expiration date")
    @action(detail=False, 
            methods=['patch'], 
            url_path="update_all_users_due_date", 
            serializer_class=ClubSerializers.UpdateClubSubscriptionDueDateSerializer,
            permission_classes=[])
    def update_all_users_due_date(self, request):
        user = request.user
        if user.role not in ["main_admin", "superuser"]:
            return Response(
                {"error": "Não tem autorização para realizar esta ação"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ClubSerializers.UpdateClubSubscriptionDueDateSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            quotes_to_patch = ClubSubscription.objects.filter(year=serializer.validated_data["year"])
            children_acounts = user.children.exclude(role="technician")

            for children in children_acounts:
                Notification.objects.create(type="payment_available", 
                                            notification=f'A data limite para pagamento da quota para a época {serializer.validated_data["year"]}/{int(serializer.validated_data["year"]) + 1} foi alterada.', 
                                            payment_object="quotes",
                                            can_remove=True,
                                            club_user=children)
            for quotes in quotes_to_patch:
                quotes.due_date = serializer.validated_data["due_date"]
                quotes.save()

        return Response(
            {"message": f'Data limite de {serializer.validated_data["year"]} atualizada.'},
            status=status.HTTP_200_OK
        )
    
    @extend_schema(description="An endpoint that targets all children accounts of an admin, in order to, update all subscription object if the given year," \
    "with a new amount")
    @action(detail=False, 
            methods=['patch'], 
            url_path="update_all_users_amount", 
            serializer_class=ClubSerializers.UpdateClubSubscriptionAmountSerializer,
            permission_classes=[])
    def update_all_users_amount(self, request):
        user = request.user
        if user.role not in ["main_admin", "superuser"]:
            return Response(
                {"error": "Não tem autorização para realizar esta ação"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ClubSerializers.UpdateClubSubscriptionAmountSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            quotes_to_patch = ClubSubscription.objects.filter(year=serializer.validated_data["year"])
            children_acounts = user.children.exclude(role="technician")
            for children in children_acounts:
                Notification.objects.create(type="payment_available", 
                                            notification=f'O valor para pagamento da quota para a época {serializer.validated_data["year"]}/{int(serializer.validated_data["year"]) + 1} foi alterado.', 
                                            payment_object="quotes",
                                            can_remove=True,
                                            club_user=children)
            for quotes in quotes_to_patch:
                quotes.amount = serializer.validated_data["amount"]
                quotes.save()

        return Response(
            {"message": f'Valores de {serializer.validated_data["year"]} atualizados para {serializer.validated_data["amount"]}€'},
            status=status.HTTP_200_OK
        )

    @extend_schema(description="An endpoint that targets all children accounts of an admin, in order to create new subscription objects in the given year")
    @action(detail=False, 
            methods=['post'], 
            url_path="create_all_users", 
            serializer_class=ClubSerializers.CreateAllClubsSubscriptionSerializer,
            permission_classes=[])
    def create_all_users(self, request):
        user = request.user
        amount = ClubSubscriptionConfig.get_amount_for(user)
        if user.role not in ["main_admin", "superuser"]:
            return Response(
                {"error": "Não tem autorização para realizar esta ação"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ClubSerializers.CreateAllClubsSubscriptionSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            children_acounts = user.children.exclude(role="technician")
            if len(children_acounts) == 0:
                return Response(
                    {"error": "Não possui nenhuma conta filha."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            year = serializer.validated_data["year"]
            last_day_of_year = datetime(year=int(year) - 1, month=12, day=31, tzinfo=timezone.get_current_timezone())
            if year < date.today().year:
                return Response(
                    {"error": "Não pode criar notifcações de quotas para anos anteriores ao atual."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            for children in children_acounts:
                Notification.objects.create(type="payment_available", 
                                            notification=f'O pagamento da quota para a época {year}/{int(year) + 1} já se encontra disponível.', 
                                            payment_object="quotes",
                                            club_user=children)
                ClubSubscription.objects.create(**serializer.validated_data, amount=amount, due_date=last_day_of_year, club=children)
        return Response(
            {"message": "Criadas Notificações de pagamento para todos os Clubes."},
            status=status.HTTP_200_OK
        )