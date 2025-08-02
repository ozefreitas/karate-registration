from django.shortcuts import render
from core.permissions import IsAuthenticatedOrReadOnly, IsNationalForPostDelete
from .models import Category, SignupToken
from . import serializers
from django.utils import timezone

from rest_framework.decorators import action, permission_classes, api_view
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework import viewsets, filters, status, views
from rest_framework.permissions import IsAuthenticated, IsAdminUser

# Create your views here.

class MultipleSerializersMixIn:
    serializer_classes = {}

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, self.serializer_class)
    

class CategoriesViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    queryset=Category.objects.all()
    serializer_class=serializers.CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    serializer_classes = {
        "create": serializers.CreateCategorySerializer,
        "retrieve": serializers.CompactCategorySerializer
    }

    @action(detail=False, methods=['delete'], url_path="delete_all")
    def delete_all(self, request):
        # CAREFUL as all categories is for now the onlu ones
        deleted_count, _ = Category.objects.all().delete()
        if deleted_count <= 1:
            return Response(
                {"message": "Escalão eliminado"},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"message": f"Eliminados {deleted_count} Escalões"},
                status=status.HTTP_200_OK
            )
        
@extend_schema(
        request=serializers.GenerateTokenSerializer,
        responses={201: None, 400: None},
        description="Generate a unique token with an expiration date to allow for sign up."
    )
@api_view(['POST'])
# @authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated, IsAdminUser])
def sign_up_token(request):
    username = request.data.get('username')
    alive_time = request.data.get('alive_time')
    token = SignupToken.objects.create(username=username, alive_time=alive_time if alive_time != 0 else 3)
    return Response({"username": username, "token": str(token.token)})

@extend_schema(
        request=serializers.TokenSerializer,
        responses={200: None, 400: None},
        description="Given the token provided in the URL, simply return the username associated with it."
    )
@api_view(['get'])
# @authentication_classes([SessionAuthentication, BasicAuthentication])
def get_token_username(request):
    token = request.query_params.get('token')
    token_obj = SignupToken.objects.get(token=token)
    return Response({"username": token_obj.username})

@api_view(['GET'])
def current_season(request):
    today = timezone.now()
    if today.month > 8:
        season = f"{today.year} - {today.year + 1}"
    else:
        season = f"{today.year - 1}-{today.year}"
    return Response({"season": season})


class UserDetailView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
        }, status=status.HTTP_200_OK)
    

class LogoutView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()  # Deletes token from DB
        return Response({"detail": "Logged out"}, status=200)

class RegisterView(views.APIView):
    @extend_schema(
        request=serializers.RegisterUserSerializer,
        responses={201: None, 400: None},
        description="Register a new user with username, email and password."
    )
    def post(self, request):
        serializer = serializers.RegisterUserSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
