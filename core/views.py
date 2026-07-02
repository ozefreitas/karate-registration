from django.utils import timezone
from django.db import transaction
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404

from .filters import NotificationsFilters, CategoriesFilters
from core.permissions import IsAuthenticatedOrReadOnly, IsUnauthenticatedForPost, IsNationalForPostDelete, IsAdminRoleorHigher, IsPayingUserorAdminForGet, CanFilterByUserPermission, MemberValidationRequestPermissions
from .models import Category, SignupToken, RequestedAcount, User, RequestPasswordReset, MemberValidationRequest, Notification, FeedbackData
from clubs.models import Club
from .models import Notification, MonthlyPaymentPlan, MemberValidationRequest
from core.serializers import base as BaseSerializers
from core.serializers.categories import CategorySerializer, CreateCategorySerializer, CompactCategorySerializer
from core.serializers.users import UsersSerializer, UserDetailSerializer, UsersResponseSerializer

from rest_framework.authtoken.models import Token
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.exceptions import ValidationError
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action, permission_classes, api_view
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework.response import Response
from rest_framework import viewsets, filters, status, views, serializers
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.exceptions import PermissionDenied

# Create your views here.

class MultipleSerializersMixIn:
    serializer_classes = {}

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, self.serializer_class)


class NotificationViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    queryset=Notification.objects.all()
    serializer_class=BaseSerializers.NotificationsSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsNationalForPostDelete, CanFilterByUserPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ["notification", "type", "created_at"]
    filterset_class = NotificationsFilters

    serializer_classes = {
        "create": BaseSerializers.CreateNotificationsSerializer,
    }

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return Notification.objects.none()

        # if admin can see everything
        if user.role in ["main_admin", "single_admin", "superuser"]:
            return Notification.objects.all().order_by("-created_at")

        # normal users -> only their own
        return Notification.objects.filter(club_user=user).order_by("-created_at")
    
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


class NotificationsView(GenericAPIView):
    serializer_class = BaseSerializers.NotificationsSerializer
    permission_classes = [
        IsAuthenticated,
        IsPayingUserorAdminForGet
    ]

    def get_queryset(self):
        return Notification.objects.filter(
            club_user=self.request.user
        ).order_by("-created_at")

    @extend_schema(
        responses=inline_serializer(
            name="NotificationsResponse",
            fields={
                "response": BaseSerializers.NotificationsSerializer(many=True),
                "total": serializers.IntegerField(),
            },
        )
    )
    def get(self, request):
        qs = self.get_queryset()

        serializer = self.get_serializer(
            qs[:5],
            many=True
        )

        return Response({
            "response": serializer.data,
            "total": qs.count()
        })

    

class CategoriesViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    queryset=Category.objects.all().order_by("min_age", "min_weight")
    serializer_class=CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ["min_age", "max_age", "min_grad", "max_grad", "min_weight", "max_weight", "name"]
    filterset_class = CategoriesFilters

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


class MemberValidationRequestViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    queryset=MemberValidationRequest.objects.all().order_by("-created_at")
    serializer_class=BaseSerializers.MemberValidationRequestSerializer
    permission_classes = [MemberValidationRequestPermissions]
    filter_backends = [DjangoFilterBackend]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    serializer_classes = {
        "create": BaseSerializers.CreateMemberValidationRequestSerializer,
        "partial_update": BaseSerializers.PatchMemberValidationRequestSerializer
    }

    def perform_create(self, serializer):
        user = self.request.user

        person = serializer.validated_data["person"]
        
        request_type = serializer.validated_data["request_type"]
        serializer.save(requested_by=user, person=person)

        if request_type == "verify":
            Notification.objects.create(
                type="member_request",
                notification=(
                    f'O Membro {person.first_name} {person.last_name} do Clube {person.club.username} '
                    f'está à espera de Validação.'
                ),
                target_person=person,
                club_user=person.club.parent,
                can_remove=True
            )

            try:
                Notification.objects.get(type="member_updated", target_person=person, club_user=user).delete()
            except Exception:
                pass

        elif request_type == "exams":
            Notification.objects.create(
                type="exam_prop",
                notification=(
                    f'O Clube {person.club.username} enviou uma Proposta de Exame para o Membro {person.first_name} {person.last_name}.'
                ),
                target_person=person,
                club_user=person.club.parent,
                can_remove=True
            )

            try:
                Notification.objects.get(type="member_updated", target_person=person, club_user=user).delete()
            except Exception:
                pass


    def perform_update(self, serializer):
        instance = self.get_object()
        person = instance.person
        person_club = person.club
        status = serializer.validated_data["status"]
        request_type = serializer.validated_data["request_type"]
        admin_comment = serializer.validated_data["admin_comment"]
        if status == "approved" and request_type == "verify":
            person.is_validated = True
            person.updated_by = self.request.user
            person.save()

            if admin_comment != "" or admin_comment != None:
                notification = (f'A Validação do Membro {person.first_name} {person.last_name} foi aceite pelo seu administrador com a seguinte mensagem: {serializer.validated_data["admin_comment"]}. '
                'Este Membro está agora "Verificado" e pode ser inscrito em Eventos e ser proposto a exames de graduação.')
            else:
                notification = (f'A Validação do Membro {person.first_name} {person.last_name} foi aceite pelo seu administrador. '
                'Este Membro está agora "Verificado" e pode ser inscrito em Eventos e ser proposto a exames de graduação.')
            Notification.objects.create(type="member_updated",
                                        notification=notification,
                                        target_person=person,
                                        can_remove=True,
                                        club_user=person_club,
                                        )

        elif status != "approved" and request_type == "verify":
            if admin_comment != "" or admin_comment != None:
                notification = f'A Validação do Membro {person.first_name} {person.last_name} foi rejeitada pelo seu administrador com a seguinte mensagem: {serializer.validated_data["admin_comment"]}. '
            else:
                notification = f'A Validação do Membro {person.first_name} {person.last_name} foi rejeitada pelo seu administrador.'
            Notification.objects.create(type="member_updated",
                                        notification=notification,
                                        target_person=person,
                                        can_remove=True,
                                        club_user=person_club,
                                        )
        
        elif status == "approved" and request_type == "exams":
            if admin_comment != "" or admin_comment != None:
                notification = (f'A Proposta de Exame do {person.first_name} {person.last_name} foi aceite pelo seu administrador com a seguinte mensagem: {serializer.validated_data["admin_comment"]}. '
                'Este Membro transitou agora para a graduação proposta.')
            else:
                notification = (f'A Proposta de Exame {person.first_name} {person.last_name} foi aceite pelo seu administrador. '
                'Este Membro transitou agora para a graduação proposta.')
            Notification.objects.create(type="member_updated",
                                        notification=notification,
                                        target_person=person,
                                        can_remove=True,
                                        club_user=person_club,
                                        )
        
        elif status != "approved" and request_type == "exams":
            if admin_comment != "" or admin_comment != None:
                notification = f'A Proposta de Exame do Membro {person.first_name} {person.last_name} foi rejeitada pelo seu administrador com a seguinte mensagem: {serializer.validated_data["admin_comment"]}.'
            else:
                notification = f'A Proposta de Exame do Membro {person.first_name} {person.last_name} foi rejeitada pelo seu administrador.'
            Notification.objects.create(type="member_updated",
                                        notification=notification,
                                        target_person=person,
                                        can_remove=True,
                                        club_user=person_club,
                                        )

        serializer.save(reviewed_by=self.request.user, reviewed_at=timezone.now())

        try:
            Notification.objects.get(type="member_request", target_person=person, club_user=person_club).delete()
        except Exception:
            pass


class MonthlyPaymentPlanViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    queryset=MonthlyPaymentPlan.objects.all().order_by("name")
    serializer_class=BaseSerializers.MonthlyPaymentPlanSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    serializer_classes = {
        "create": BaseSerializers.CreateMonthlyPaymentPlanSerializer,
    }

    def get_queryset(self):
        user = self.request.user
        return self.queryset.filter(club_user=user)
    
    def perform_create(self, serializer):
        user = self.request.user
        if user.role != "subed_club":
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer.save(club_user=user)

    def perform_destroy(self, instance):
        if instance.is_default:
            raise ValidationError({
                "detail": "Não pode apagar um Plano padrão. Altere primeiro outro plano para padrão e tente novamente."
            })
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

@extend_schema(
    responses=BaseSerializers.CurrentSeasonSerializer,
    description=(
        "Typical sportif season change in August. "
        "This endpoint checks the current month and returns the respective season."
    ),
)
class CurrentSeasonView(GenericAPIView):
    serializer_class = BaseSerializers.CurrentSeasonSerializer

    def get(self, request):
        today = timezone.now()
        if today.month > 8:
            season = f"{today.year}-{today.year + 1}"
        else:
            season = f"{today.year - 1}-{today.year}"

        serializer = self.get_serializer({"season": season})
        return Response(serializer.data)


@extend_schema(responses=UserDetailSerializer)
class UserDetailView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserDetailSerializer

    def get(self, request):
        user = request.user
        data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "tier": user.tier,
        }
        serializer = self.get_serializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class CustomAuthToken(ObtainAuthToken):
    serializer_class = BaseSerializers.AuthLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']
        user = User.objects.get(username=username)
        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)
        return Response(BaseSerializers.TokenSerializer({'token': token.key}).data)
    

class LogoutView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BaseSerializers.LogoutResponseSerializer

    @extend_schema(
        request=None,
        responses=BaseSerializers.LogoutResponseSerializer,
        description="Logs out the authenticated user by deleting their auth token."
    )
    def post(self, request):
        request.user.auth_token.delete()
        serializer = self.get_serializer({"detail": "Logged out"})
        return Response(serializer.data)


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
                RequestedAcount.objects.filter(username=serializer.validated_data.get('username')).delete()
                serializer.save()
                return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)
            else:
                RequestedAcount.objects.filter(username=serializer.validated_data.get('username')).delete()
                Notification.objects.filter(type="request", request_acount=serializer.validated_data.get('username')).delete()
                serializer.save()
                return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    description="Lists users or fetches a specific user by username.",
    responses=UsersSerializer(many=True),
)
class UsersView(GenericAPIView):
    permission_classes = [IsAuthenticated, IsAdminRoleorHigher]
    serializer_class = UsersSerializer

    def get(self, request):
        username = request.query_params.get("username")
        if username:
            user = get_object_or_404(User, username=username)
            serializer = self.get_serializer(user)
            return Response(serializer.data)

        queryset = User.objects.filter(role__in=["free_club", "subed_club"])
        serializer = self.get_serializer(queryset, many=True)
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


@extend_schema(
    request=BaseSerializers.RequestPasswordResetSerializer,
    responses={
        201: BaseSerializers.RequestPasswordResetResponseSerializer,
        400: BaseSerializers.RequestPasswordResetResponseSerializer,
    },
    description="Creates a new request for a password recovery."
)
class RequestPasswordResetView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = BaseSerializers.RequestPasswordResetSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username_or_email = serializer.validated_data.get("username_or_email")

        try:
            user = User.objects.get(
                Q(username=username_or_email) |
                Q(email=username_or_email)
            )
        except User.DoesNotExist:
            return Response(
                {"message": "No user found with these credentials."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if RequestPasswordReset.objects.filter(club_user=user).exists():
            return Response(
                {"message": "Reset already requested. Wait for admin email."},
                status=status.HTTP_400_BAD_REQUEST
            )

        RequestPasswordReset.objects.create(club_user=user)
        admin_user = User.objects.get(role="main_admin")
        Notification.objects.create(
            club_user=admin_user,
            notification=(f"Password reset request from {user.username} was initiated."),
            type="reset",
            request_acount=user.username
        )

        return Response(
            {"message": "Request sent! Check your email."},
            status=status.HTTP_201_CREATED
        )


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


###############
# Request passorwd reset
###############


class FeedbackViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    queryset=FeedbackData.objects.all().order_by("created_at")
    serializer_class=BaseSerializers.FeedbackSerializer
    # permission_classes = [IsAuthenticated]
    pagination_class = None

    serializer_classes = {
        "create": BaseSerializers.CreateFeedbackSerializer,
    }

    # def get_queryset(self):
    #     user = self.request.user
    #     return self.queryset.filter(club_user=user)

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(club_user=user)


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