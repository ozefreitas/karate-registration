from django.utils import timezone
from django.db import transaction
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend

from .filters import NotificationsFilters
from core.permissions import IsAuthenticatedOrReadOnly, IsUnauthenticatedForPost, IsNationalForPostDelete, IsAdminRoleorHigher, IsPayingUserorAdminForGet
from .models import Category, SignupToken, RequestedAcount, User, RequestPasswordReset
from clubs.models import Club
from .models import Notification
from core.serializers import base as BaseSerializers
from core.serializers.categories import CategorySerializer, CreateCategorySerializer, CompactCategorySerializer
from core.serializers.users import UsersSerializer

from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action, permission_classes, api_view
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework import viewsets, filters, status, views, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView

# Create your views here.

class MultipleSerializersMixIn:
    serializer_classes = {}

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, self.serializer_class)


class NotificationViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    queryset=Notification.objects.all()
    serializer_class=BaseSerializers.NotificationsSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsNationalForPostDelete]
    filter_backends = [DjangoFilterBackend]
    # filterset_class = NotificationsFilters

    serializer_classes = {
        "create": BaseSerializers.CreateNotificationsSerializer,
        # "update": CoreSerializers.UpdateEventSerializer
    }

    def get_queryset(self):
        user = self.request.user
        return Notification.objects.filter(club_user=user) .order_by("created_at")
    
    @action(detail=False, methods=['post'], url_path="create_all_users", serializer_class=BaseSerializers.AllUsersNotificationsSerializer)
    def create_all_user(self, request):
        user = request.user
        if user.role not in ["main_admin", "superuser"]:
            return Response(
                {"error": "Não tem autorização para realizar esta ação"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = BaseSerializers.AllUsersNotificationsSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            children_acounts = user.children.exclude(role="technician")
            if len(children_acounts) == 0:
                return Response(
                    {"error": "Não possui nenhuma conta filha."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            for children in children_acounts:
                Notification.objects.create(**serializer.validated_data, club_user=children)
        return Response(
            {"message": "Notificações enviadas para todos os clubes."},
            status=status.HTTP_200_OK
        )


@api_view(['GET'])
# @authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated, IsPayingUserorAdminForGet])
def notifications(request):
    notifications = Notification.objects.filter(club_user=request.user)[:5]
    serializer = BaseSerializers.NotificationsSerializer(notifications, many=True)
    return Response(serializer.data)
    

class CategoriesViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    queryset=Category.objects.all().order_by("min_age")
    serializer_class=CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    serializer_classes = {
        "create": CreateCategorySerializer,
        "retrieve": CompactCategorySerializer
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
    serializer_class=BaseSerializers.RequestedAcountSerializer
    permission_classes = [IsUnauthenticatedForPost]

    def perform_create(self, serializer):
        username = serializer.validated_data.get('username')

        try:
            club_name = Club.objects.get(name=username)
        except Club.DoesNotExist:
            raise serializers.ValidationError(f"No Club found with '{username}' username")

        if club_name.is_registered:
            raise serializers.ValidationError(f"Club '{username}' is already registered.")

        # Mark as registered
        club_name.is_registered = True
        club_name.save()
        if club_name.is_admin:
            serializer.save()
        else:
            admin_user = User.objects.get(role="main_admin")
            Notification.objects.create(name=admin_user, 
                                        notification=f'Um pedido de criação de conta com o username {username} foi inciado. Dirija-se para a área de Definições na aba "Gestor de Contas".',
                                        type="request", 
                                        request_acount=username)

            # Save the RequestedAcount instance normally
            serializer.save()

    def perform_destroy(self, instance):
        with transaction.atomic():
            club_name = Club.objects.filter(name=instance.username).first()
            if club_name:
                club_name.is_registered = False
                club_name.save()

            Notification.objects.filter(
                type="request",
                request_acount=instance.username 
            ).delete()

            instance.delete()

        
@extend_schema(
        request=BaseSerializers.GenerateTokenSerializer,
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
        request=BaseSerializers.TokenSerializer,
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
        request=BaseSerializers.UsernameSerializer,
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
    

class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        # Delete old token (if exists) and create new one
        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)
        return Response({'token': token.key})
    

class LogoutView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()  # Deletes token from DB
        return Response({"detail": "Logged out"}, status=200)


class RegisterView(views.APIView):
    @extend_schema(
        request=BaseSerializers.RegisterUserSerializer,
        responses={201: None, 400: None},
        description="Register a new user with username, email and password."
    )
    def post(self, request):
        serializer = BaseSerializers.RegisterUserSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            club_obj = Club.objects.get(name=serializer.validated_data.get('username'))
            if club_obj.is_admin:
                serializer.save()
                RequestedAcount.objects.filter(username=serializer.validated_data.get('username')).delete()
                return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)
            else:
                RequestedAcount.objects.filter(username=serializer.validated_data.get('username')).delete()
                Notification.objects.filter(type="request", request_acount=serializer.validated_data.get('username')).delete()
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
        serializer = UsersSerializer(user)
    else:
        users = User.objects.filter(role__in=["free_club", "subed_club"])
        serializer = UsersSerializer(users, many=True)
    return Response(serializer.data)



###############
# Request passorwd reset
###############

@extend_schema(
        request=BaseSerializers.PasswordRequestsSerializer,
        responses={200: None, 400: None},
        description="Returns all the current requests for password resets."
    )
@api_view(['GET'])
@permission_classes([IsAdminRoleorHigher])
def get_password_requests(request):
    requests = RequestPasswordReset.objects.all()
    serializer = BaseSerializers.PasswordRequestsSerializer(requests, many=True)
    return Response(serializer.data)


@extend_schema(request=BaseSerializers.RequestPasswordResetSerializer, 
               description="Creates a new request for a password recovery.")
@api_view(['POST'])
def request_password_reset(request):
    serializer = BaseSerializers.RequestPasswordResetSerializer(data=request.data)
    if serializer.is_valid(raise_exception=True):
        try:
            user = User.objects.get(
                Q(username=serializer.validated_data.get('username_or_email')) | Q(email=serializer.validated_data.get('username_or_email'))
            )
        except User.DoesNotExist:
            return Response({"error": "Não existe nenhum utilizador com estas credenciais!"}, status=status.HTTP_400_BAD_REQUEST)
    if RequestPasswordReset.objects.filter(club_user=user).exists():
        return Response({"error": "Já fez o pedido para recuperar a sua password. Aguarde por um email do seu administrador!"}, status=status.HTTP_400_BAD_REQUEST)
    RequestPasswordReset.objects.create(club_user=user)
    admin_user = User.objects.get(role="main_admin")
    Notification.objects.create(club_user=admin_user, 
                                    notification=f'Um pedido de recuperção de password de {user.username} foi inciado. Dirija-se para a área de Definições na aba "Gestor de Contas" imediatamente!',
                                    type="reset", 
                                    request_acount=user.username)
    return Response({"message": "Pedido enviado! Esteja atento ao seu email."}, status=status.HTTP_201_CREATED)


@extend_schema(
        request=BaseSerializers.UsernameSerializer,
        responses={201: None, 400: None},
        description="Generate a unique url for password recovery by providing the id of the account."
    )
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminRoleorHigher])
def generate_password_recovery_url(request):
    serializer = BaseSerializers.UsernameSerializer(data=request.data)
    if serializer.is_valid(raise_exception=True):
        try:
            user = User.objects.get(id=serializer.validated_data.get('username'))
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            # reset_url = request.build_absolute_uri(
            #     reverse("password_reset_confirm", kwargs={"uidb64": uid, "token": token})
            # )

            # Just returns the link expected in the frontend
            return Response({"url": f"/reset/{uid}/{token}/"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": "Ocorreu um erro."}, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmAPI(views.APIView):
    @extend_schema(
        request=BaseSerializers.PasswordSerializer,
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
        RequestPasswordReset.objects.filter(club_user=user).delete()
        return Response({"success": True})


#############
# JWT Authentication
#############

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            refresh = response.data["refresh"]

            # move refresh token to cookie
            res = Response({"access": response.data["access"]})
            res.set_cookie(
                key="refresh_token",
                value=refresh,
                httponly=True,
                secure=True,          # only HTTPS
                samesite="Strict",    # CSRF protection
                max_age=7*24*60*60,   # 7 days
            )
            return res
        return response
