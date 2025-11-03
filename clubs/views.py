from django.conf import settings
from django.db.models import Q, Count
from django.contrib.auth import get_user_model

from .models import Club
from .serializers import ClubsSerializer, CreateClubSerializer
from core.permissions import IsGETforClubs, IsAdminRoleorHigher
from core.views import MultipleSerializersMixIn

from rest_framework import viewsets, filters, status
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework. views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, action

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
def club_athletes(request):
    data = User.objects.exclude(role__in=["main_admin", "superuser"])\
                        .annotate(athlete_count=Count('athlete'))\
                        .values('username', 'athlete_count')
    return Response(data)