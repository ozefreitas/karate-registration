from django.conf import settings
from django.db.models import Q, Count, Case, When, IntegerField
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