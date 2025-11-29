from django.conf import settings
from django.db.models import Q, Count, Case, When, IntegerField
from django.contrib.auth import get_user_model

from .models import Club, ClubSubscription
from core.models import Notification
from .serializers import ClubsSerializer, CreateClubSerializer, ClubSubscriptionsSerializer, CreateClubSubscriptionSerializer, CreateAllClubsSubscriptionSerializer, PatchClubSubscriptionSerializer
from core.permissions import IsGETforClubs, IsAdminRoleorHigher
from core.views import MultipleSerializersMixIn

from rest_framework import viewsets, filters, status
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework. views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, action

from datetime import date

# Create your views here.

User = get_user_model()

class ClubsViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    queryset=Club.objects.all()
    serializer_class=ClubsSerializer
    permission_classes = [IsGETforClubs]

    serializer_classes = {
        "create": CreateClubSerializer,
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
    serializer_class=ClubSubscriptionsSerializer
    permission_classes = [IsAdminRoleorHigher]
    filter_backends = [filters.SearchFilter]
    search_fields = ['year']
    pagination_class = None
    serializer_classes = {
        "create": CreateClubSubscriptionSerializer,
        "partial_update": PatchClubSubscriptionSerializer
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
        

    @action(detail=False, methods=['post'], url_path="create_all_users", serializer_class=CreateAllClubsSubscriptionSerializer)
    def create_all_users(self, request):
        user = request.user
        if user.role not in ["main_admin", "superuser"]:
            return Response(
                {"error": "Não tem autorização para realizar esta ação"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = CreateAllClubsSubscriptionSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            children_acounts = user.children.exclude(role="technician")
            if len(children_acounts) == 0:
                return Response(
                    {"error": "Não possui nenhuma conta filha."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if serializer.validated_data["year"] < date.today().year:
                return Response(
                    {"error": "Não pode criar notifcações de quotas para anos anteriores ao atual."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            for children in children_acounts:
                Notification.objects.create(type="payment_available", 
                                            notification=f'O pagamento da quota para a época {serializer.validated_data["year"]}/{int(serializer.validated_data["year"]) + 1} já se encontra disponível.', 
                                            payment_object="quotes",
                                            club_user=children)
                ClubSubscription.objects.create(**serializer.validated_data, club=children)
        return Response(
            {"message": "Criadas Notificações de pagamento para todos os Clubes."},
            status=status.HTTP_200_OK
        )