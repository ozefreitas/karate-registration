from django.utils import timezone
from django.db import transaction
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.db.models import Q

from core.permissions import IsAuthenticatedOrReadOnly, IsUnauthenticatedForPost, IsNationalForPostDelete, IsAdminRoleorHigher
from .models import Category, SignupToken, RequestedAcount, User, RequestPasswordReset
from registration.models import Dojo
from dojos.models import Notification
from . import serializers

from rest_framework.decorators import action, permission_classes, api_view
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework import viewsets, filters, status, views
from rest_framework.permissions import IsAuthenticated

# Create your views here.

class MultipleSerializersMixIn:
    serializer_classes = {}

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, self.serializer_class)
    

class CategoriesViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    queryset=Category.objects.all().order_by("min_age")
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


class RequestedAcountViewSet(viewsets.ModelViewSet):
    queryset=RequestedAcount.objects.all()
    serializer_class=serializers.RequestedAcountSerializer
    permission_classes = [IsUnauthenticatedForPost]

    def perform_create(self, serializer):
        username = serializer.validated_data.get('username')

        try:
            dojo = Dojo.objects.get(dojo=username)
        except Dojo.DoesNotExist:
            raise serializers.ValidationError(f"No Dojo found with dojo '{username}'")

        if dojo.is_registered:
            raise serializers.ValidationError(f"Dojo '{username}' is already registered.")

        # Mark as registered
        dojo.is_registered = True
        dojo.save()
        if dojo.is_admin:
            serializer.save()
        else:
            admin_user = User.objects.get(role="main_admin")
            Notification.objects.create(dojo=admin_user, 
                                        notification=f'Um pedido de criação de conta com o username {username} foi inciado. Dirija-se para a área de Definições na aba "Gestor de Contas".',
                                        urgency="red",
                                        type="request", 
                                        request_acount=username)

            # Save the RequestedAcount instance normally
            serializer.save()

    def perform_destroy(self, instance):
        with transaction.atomic():
            dojo = Dojo.objects.filter(dojo=instance.username).first()
            if dojo:
                dojo.is_registered = False
                dojo.save()

            Notification.objects.filter(
                type="request",
                request_acount=instance.username 
            ).delete()

            instance.delete()

        
@extend_schema(
        request=serializers.GenerateTokenSerializer,
        responses={201: None, 400: None},
        description="Generate a unique token with an expiration date to allow for sign up."
    )
@api_view(['POST'])
# @authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated, IsNationalForPostDelete])
def sign_up_token(request):
    username = request.data.get('username')
    alive_time = request.data.get('alive_time', 3)
    token = SignupToken.objects.create(username=username, alive_time=alive_time)
    return Response({"username": username, "token": str(token.token)})

@extend_schema(
        request=serializers.TokenSerializer,
        responses={200: None, 400: None},
        description="Given the token provided in the URL, simply return the username associated with it."
    )
@api_view(['GET'])
# @authentication_classes([SessionAuthentication, BasicAuthentication])
# @permission_classes([IsUnauthenticatedForPost])
def get_token_username(request):
    token = request.query_params.get('token')
    token_obj = SignupToken.objects.get(token=token)
    return Response({"username": token_obj.username})

@extend_schema(
        request=serializers.UsernameSerializer,
        responses={200: None, 400: None},
        description="Given a username with a token, returns the token. This is usefull for the admin to go back and get the token again if the page reloads."
    )
@api_view(['GET'])
# @authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsUnauthenticatedForPost])
def get_token_by_username(request):
    username = request.query_params.get('username', None)
    try:
        token_obj = SignupToken.objects.get(username=username)
        return Response({"token": token_obj.token})
    except SignupToken.DoesNotExist:
        return Response({"error": "Provided username does not exist"})

@api_view(['GET'])
@extend_schema(
        responses={200: None, 400: None},
        description="Typical sportif season change in August. This endpoints checks the current month and return the respective season."
    )
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
            club_obj = Dojo.objects.get(dojo=serializer.validated_data.get('username'))
            if club_obj.is_admin:
                serializer.save()
                return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)
            else:
                request_obj = RequestedAcount.objects.get(username=serializer.validated_data.get('username'))
                request_obj.delete()
                notification_obj = Notification.objects.get(type="request", request_acount=serializer.validated_data.get('username'))
                notification_obj.delete()
                serializer.save()
                return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(description="Lists the current users available users.")
@api_view(['GET'])
# @authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated, IsAdminRoleorHigher])
def users(request):
    username = request.query_params.get('username', None)
    if username:
        user = User.objects.get(username=username)
        serializer = serializers.UsersSerializer(user)
    else:
        users = User.objects.filter(role__in=["free_dojo", "subed_dojo"])
        serializer = serializers.UsersSerializer(users, many=True)
    return Response(serializer.data)



###############
# Request passorwd reset
###############

@extend_schema(
        request=serializers.PasswordRequestsSerializer,
        responses={200: None, 400: None},
        description="Returns all the current requests for password resets."
    )
@api_view(['GET'])
# @authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAdminRoleorHigher])
def get_password_requests(request):
    requests = RequestPasswordReset.objects.all()
    serializer = serializers.PasswordRequestsSerializer(requests, many=True)
    return Response(serializer.data)


@extend_schema(request=serializers.RequestPasswordResetSerializer, 
               description="Creates a new request for a password recovery.")
@api_view(['POST'])
def request_password_reset(request):
    serializer = serializers.RequestPasswordResetSerializer(data=request.data)
    if serializer.is_valid(raise_exception=True):
        try:
            user = User.objects.get(
                Q(username=serializer.validated_data.get('username_or_email')) | Q(email=serializer.validated_data.get('username_or_email'))
            )
        except User.DoesNotExist:
            return Response({"error": "Não existe nenhum utilizador com estas credenciais!"}, status=status.HTTP_400_BAD_REQUEST)
    if RequestPasswordReset.objects.filter(dojo_user=user).exists():
        return Response({"error": "Já fez o pedido para recuperar a sua password. Aguarde por um email do seu administrador!"}, status=status.HTTP_400_BAD_REQUEST)
    RequestPasswordReset.objects.create(dojo_user=user)
    admin_user = User.objects.get(role="main_admin")
    Notification.objects.create(dojo=admin_user, 
                                    notification=f'Um pedido de recuperção de password de {user.username} foi inciado. Dirija-se para a área de Definições na aba "Gestor de Contas" imediatamente!',
                                    urgency="red",
                                    type="reset", 
                                    request_acount=user.username)
    return Response({"message": "Pedido enviado! Esteja atento ao seu email."}, status=status.HTTP_201_CREATED)


@extend_schema(
        request=serializers.UsernameSerializer,
        responses={201: None, 400: None},
        description="Generate a unique url for password recovery."
    )
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminRoleorHigher])
def generate_password_recovery_url(request):
    serializer = serializers.UsernameSerializer(data=request.data)
    if serializer.is_valid(raise_exception=True):
        user = User.objects.get(id=serializer.validated_data.get('username'))
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        reset_url = request.build_absolute_uri(
            reverse("password_reset_confirm", kwargs={"uidb64": uid, "token": token})
        )
        return Response({"url": reset_url})


class PasswordResetConfirmAPI(views.APIView):
    @extend_schema(
        request=serializers.PasswordSerializer,
        responses={201: None, 400: None},
        description="View that confirms the uidb64 and token from the requesting user, and checks if a password is provided in the payload."
    )
    def post(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"error": "Link inválido"}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({"error": "Token inválido ou expirado"}, status=status.HTTP_400_BAD_REQUEST)

        new_password = request.data.get("password")
        new_password2 = request.data.get("password2")
        if not new_password:
            return Response({"error": "Forneça uma palavra-passe"}, status=status.HTTP_400_BAD_REQUEST)
        if not new_password2:
            return Response({"error": "Repita a palavra-passe para confirmação"}, status=status.HTTP_400_BAD_REQUEST)
        
        if new_password != new_password2:
            return Response({"error": "As palavras-passe não coincidem!"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        Notification.objects.filter(type="reset", request_acount=user.username).delete()
        RequestPasswordReset.objects.filter(dojo_user=user).delete()
        return Response({"success": True})
