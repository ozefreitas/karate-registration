from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.template.loader import render_to_string
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from .forms import DojoRegisterForm, DojoUpdateForm, ProfileUpdateForm, FeedbackForm, DojoPasswordResetForm, DojoPasswordConfirmForm, DojoPasswordChangeForm
from .permissions import IsAuthenticatedOrReadOnly
from .models import Event, Notification, DojosRatingAudit
from registration.models import Dojo, Athlete, Team
from smtplib import SMTPException
from dojos import serializers

from rest_framework import viewsets, filters, status
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework. views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, action
from drf_spectacular.utils import extend_schema

class MultipleSerializersMixIn:
    serializer_classes = {}

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, self.serializer_class)


class CompetitionViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    queryset=Event.objects.all()
    serializer_class=serializers.CompetitionsSerializer
    # authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    serializer_classes = {
        "create": serializers.CreateCompetitionSerializer,
        "update": serializers.UpdateCompetitionSerializer
    }

    def get_queryset(self):
        return self.queryset.order_by("competition_date")

    @action(detail=False, methods=["get"], url_path="next_comp")
    def next_comp(self, request):
        next_competition = Event.objects.filter(has_ended=False).order_by('competition_date').first()
        if next_competition is None:
            return Response([])
        serializer = serializers.CompetitionsSerializer(next_competition)
        return Response(serializer.data)
    
    @action(detail=False, methods=["get"], url_path="last_comp")
    def last_comp(self, request):
        last_competition = Event.objects.filter(has_ended=True).order_by('competition_date').last()
        if last_competition is None:
            return Response([])
        serializer = serializers.CompetitionsSerializer(last_competition)
        return Response(serializer.data)
    
    @action(detail=True, methods=["post"], url_path="add_athlete", serializer_class=serializers.AddAthleteSerializer, permission_classes=[IsAuthenticated])
    def add_athlete(self, request, pk=None):
        event = self.get_object()
        serializer = serializers.AddAthleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        athlete_id = serializer.validated_data["athlete_id"]

        try:
            athlete = Athlete.objects.get(id=athlete_id)
            event.individuals.add(athlete)

            return Response({"message": "Atleta adicionado a este evento!"}, status=status.HTTP_200_OK)
        except Athlete.DoesNotExist:
            return Response({"error": "Um erro ocurreu ao adicionar este Atleta!"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=["post"], url_path="delete_athlete", serializer_class=serializers.AddAthleteSerializer)
    def delete_athlete(self, request, pk=None):
        event = self.get_object()
        serializer = serializers.AddAthleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        athlete_id = serializer.validated_data["athlete_id"]

        try:
            athlete = Athlete.objects.get(id=athlete_id)
            event.individuals.remove(athlete)

            return Response({"message": "Atleta removido deste evento!"}, status=status.HTTP_200_OK)
        except Athlete.DoesNotExist:
            return Response({"error": "Um erro ocurreu ao remover este Atleta!"}, status=status.HTTP_404_NOT_FOUND)


    @action(detail=True, methods=["post"], url_path="add_team", serializer_class=serializers.AddTeamSerializer)
    def add_team(self, request):
        event = self.get_object()
        serializer = serializers.AddTeamSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        team_id = serializer.validated_data["team_id"]

        try:
            team = Team.objects.get(id=team_id)
            event.teams.add(team)

            return Response({"message": "Equipa adicionada a este evento!"}, status=status.HTTP_200_OK)
        except Athlete.DoesNotExist:
            return Response({"error": "Um erro ocurreu ao adicionar esta Equipa!"}, status=status.HTTP_404_NOT_FOUND)


    @action(detail=True, methods=["post"], url_path="delete_team", serializer_class=serializers.AddTeamSerializer)
    def delete_team(self, request, pk=None):
        event = self.get_object()
        serializer = serializers.AddTeamSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        team_id = serializer.validated_data["team_id"]

        try:
            team = Team.objects.get(id=team_id)
            event.teams.remove(team)

            return Response({"message": "Equipa removida deste evento!"}, status=status.HTTP_200_OK)
        except Athlete.DoesNotExist:
            return Response({"error": "Um erro ocurreu ao remover esta Equipa!"}, status=status.HTTP_404_NOT_FOUND)
        
        
    @action(detail=True, methods=["get"], url_path="check_event_rate", permission_classes=[IsAuthenticated])
    def check_event_rate(self, request, pk=None):
        event = self.get_object()
        if not event.has_ended:
            return Response({
                "status": "error",
                "code": "event_not_ended",
                "message": "Este Evento ainda não foi realizado."
            }, status=status.HTTP_200_OK)
        print(request.user)
        if DojosRatingAudit.objects.filter(dojo=request.user, event=event).exists():
            return Response({
                "status": "warning",
                "code": "already_rated",
                "message": "Já fez a sua avaliação deste evento."
            }, status=status.HTTP_200_OK)

        return Response({
            "status": "success",
            "code": "can_rate",
            "message": "Pode fazer a sua avaliação deste evento."
        }, status=status.HTTP_200_OK)
        

    @action(detail=True, methods=["post"], url_path="rate_event", serializer_class=serializers.RatingSerializer)
    def rate_event(self, request, pk=None):
        event = self.get_object()
        serializer = serializers.RatingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rating = serializer.validated_data["rating_signal"]
        try:
            current_rating = event.rating
            new_rating = current_rating + rating
            event.rating = new_rating
            event.save()
            DojosRatingAudit.objects.create(dojo=request.user, event=event, rating=rating)
            return Response({"message": "Obrigado pela sua opinião!"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": "Um erro ocurreu ao avaliar este Evento!"}, status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['GET'])
# @authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
def notifications(request):
    notifications = Notification.objects.filter(dojo=request.user)
    serializer = serializers.NotificationsSerializer(notifications, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def current_season(request):
    today = timezone.now()
    if today.month > 8:
        season = f"{today.year} - {today.year + 1}"
    else:
        season = f"{today.year - 1}-{today.year}"
    return Response({"season": season})


class RegisterView(APIView):
    @extend_schema(
        request=serializers.RegisterUserSerializer,
        responses={201: None, 400: None},
        description="Register a new user with username, email and password."
    )
    def post(self, request):
        serializer = serializers.RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
        }, status=status.HTTP_200_OK)
    

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()  # Deletes token from DB
        return Response({"detail": "Logged out"}, status=200)


### User loging account actions ###

def register_user(request):
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = DojoRegisterForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            form.save()
            dojo = form.cleaned_data.get("username")
            messages.success(request, f'Sucesso! Conta criada para o dojo {dojo}')
            return HttpResponseRedirect("/register/login/")
        else:
            messages.error(request, form.errors)
            return HttpResponseRedirect("/register/register_user/")

    else:
        form = DojoRegisterForm()
        return render(request, 'dojos/register_user.html', {"form": form, "title": "Criar Conta"})

def login_user(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Login efetuado com sucesso")
            return HttpResponseRedirect("/")
        else:
            messages.error(request, "Credênciais inválidas")
            messages.error(request, "Pista: O nome de utilizador tem o nome do Dojo que selecionou aquando da criação da conta")
            return HttpResponseRedirect("/register/login/")
    else:
        return render(request, "dojos/login.html", {"title": "Plataforma Login"})

@login_required
def logout_user(request):
    logout(request)
    return render(request, "dojos/logout.html")

@login_required
def profile(request):
    return render(request, 'dojos/profile.html', {"title": "Perfil"})


### Feedback view ###

def feedback(request):
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = FeedbackForm(request.POST)
        # check whether it's valid:
        if form.is_valid():

            # TODO: add notification to admin that a feedback message has just arrived
            
            form.save()
            messages.success(request, "Obrigado pelo feedback. Entrarei em contacto brevemente ")
            return HttpResponseRedirect("/")
        else:
            messages.error(request, form.errors)
            return HttpResponseRedirect("/register/feedback/")
            
    else:
        form = FeedbackForm()
        return render(request, 'dojos/feedback.html', {"form": form, "title": "Feedback"})
    

### Dojo accounts management ###
    
def update_dojo_account(request):
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form_dojo = DojoUpdateForm(request.POST, instance=request.user)
        form_profile = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        # check whether it's valid:
        if form_dojo.is_valid() and form_profile.is_valid():
            form_dojo.save()
            form_profile.save()
            messages.success(request, "Perfil atualizado com sucesso! ")
            return HttpResponseRedirect("/profile/")
        else:
            messages.error(request, form_dojo.errors)
            messages.error(request, form_profile.errors)
            return HttpResponseRedirect("/register/update_profile/")
            
    else:
        form_dojo = DojoUpdateForm(instance=request.user)
        form_profile = ProfileUpdateForm(instance=request.user.profile)
        context = {"form_dojo": form_dojo, "form_profile": form_profile, "title": "Atualizar Perfil"}
    return render(request, 'dojos/update_user.html', context)

def delete_dojo_account(request):
    if request.method == "GET":
        if not request.user.is_superuser:
            object_of = get_object_or_404(User, username=request.user.username)
            message = f'Utilizador {object_of.first_name} {object_of.last_name} eliminado com sucesso!'
            messages.success(request, message)
            object_of.delete()
            Dojo.objects.filter(dojo=request.user.username).update(is_registered=False)
            return HttpResponseRedirect("/register/register_user/")
    return HttpResponseRedirect("/")


### Password management ###

@login_required
def change_password(request):
    if request.method == "POST":
        form = DojoPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            # Important: Update the session to prevent logging out after password change
            update_session_auth_hash(request, user)
            messages.success(request, "Palavra Passe atualizada com sucesso!")
            return HttpResponseRedirect('/profile/')
        else:
            messages.error(request, form.errors)
    form = DojoPasswordChangeForm(user=request.user)
    return render(request, 'password/change_password.html', {"form": form})

def reset_password(request):
    if request.method == "POST":
        email = request.POST.get("email")
        form = DojoPasswordResetForm(request.POST)
        if form.is_valid():
            user = get_object_or_404(User, email=email)
            user = User.objects.get(email=email)
            token = PasswordResetTokenGenerator().make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            reset_url = request.build_absolute_uri(f"/register/password_reset_confirm/{uid}/{token}/")
            try:
                send_mail(
                    subject="Recuperação de Password - Karate Score App",
                    message="Está a receber este email porque pediu a recuperação da sua conta na plaforma de registos da SKI-Portugal.\n\n"
                            "Por favor, aceda ao link seguinte para continuar o processo, e escolher uma nova palavra passe.\n\n"
                            f"{reset_url}\n\n"
                            f"O seu nome de utilizador, caso se tenha esquecido, é   {user.username}.\n\n"
                            "Obrigado por usar a Karate Score App.\n"
                            "A equipa da Karate Score App:\n"
                            "José Freitas\n\n"
                            "Contactos:\n- jpsfreitas12@gmail.com / 917479331\n- info@skiportugal.pt",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
            except Exception as exc:
                raise SMTPException(exc)

            return HttpResponseRedirect("/register/password_reset/done/")
    else:
        form = DojoPasswordResetForm()
        return render(request, 'password/reset_password.html', {"form": form})
    
def password_reset_confirmation(request, 
                                uidb64, 
                                token
                                ):
    form = DojoPasswordConfirmForm()
    if request.method == "POST":
        new_password1 = request.POST.get("new_password1")
        new_password2 = request.POST.get("new_password2")
        if new_password1 != new_password2:
            messages.error(request, "Palavras passe inseridas não são iguais!")
            return render(request, "dojos/reset_password_confirm.html", {"form": form})
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
            if PasswordResetTokenGenerator().check_token(user, token):
                user.password = make_password(new_password1)
                user.save()
                return render(request, "dojos/password_reset_complete.html")
            else:
                return render(request, "Invalid or expired token.", status=400)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return render(request, "Invalid link.", status=400)
    else:
        return render(request, "password/reset_password_confirm.html", {"form": form})


### Custom error page views ###

def custom_404(request, exception):
    return render(request, 'error/404.html', status=500)

def custom_500(request):
    return render(request, 'error/500.html', status=500)

def test_500_error(request):
    raise("This is a test error")


def rules(request):
    return render(request, 'error/wip.html')
