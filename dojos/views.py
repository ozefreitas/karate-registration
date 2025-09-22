from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash, get_user_model
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count
from django.utils import timezone
from django.http import HttpResponse
from django.db.models import Q
from decouple import config
import statistics
from datetime import timedelta
import openpyxl

from .forms import DojoRegisterForm, DojoUpdateForm, ProfileUpdateForm, FeedbackForm, DojoPasswordResetForm, DojoPasswordConfirmForm, DojoPasswordChangeForm
from .filters import NotificationsFilters, DisciplinesFilters
from .models import Event, Notification, DojosRatingAudit, Discipline
from registration.models import Dojo, Athlete, Team
from core.permissions import IsAuthenticatedOrReadOnly, IsNationalForPostDelete, IsPayingUserorAdminForGet, IsGETforClubs, EventPermission, IsAdminRoleorHigherForGET, IsAdminRoleorHigher
from core.models import Category, User
from smtplib import SMTPException
from dojos import serializers
from dojos.utils.utils import calc_age
from registration.utils.utils import get_comp_age

from rest_framework import viewsets, filters, status
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework. views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, action
from drf_spectacular.utils import extend_schema

User = get_user_model()

class MultipleSerializersMixIn:
    serializer_classes = {}

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, self.serializer_class)


class EventViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    queryset=Event.objects.all()
    serializer_class=serializers.EventsSerializer
    # authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [EventPermission]

    serializer_classes = {
        "create": serializers.CreateEventSerializer,
        "update": serializers.UpdateEventSerializer
    }

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        if getattr(user, "role", None) == "free_dojo":
            now = timezone.now()
            future_7 = now + timedelta(days=7)

            qs = qs.filter(
                Q(start_registration__isnull=False, start_registration__lte=now, event_date__gte=now)
                |
                Q(start_registration__isnull=True, event_date__gte=now, event_date__lte=future_7)
            )

        return qs.order_by("event_date")
        # return self.queryset.order_by("event_date")

    def perform_create(self, serializer):
        return super().perform_create(serializer)

    @action(detail=False, methods=["get"], url_path="next_event")
    def next_event(self, request):
        next_event = Event.objects.filter(has_ended=False).order_by('event_date').first()
        if next_event is None:
            return Response([])
        serializer = serializers.EventsSerializer(next_event, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=["get"], url_path="last_event")
    def last_event(self, request):
        last_event = Event.objects.filter(has_ended=True).order_by('event_date').last()
        if last_event is None:
            return Response([])
        serializer = serializers.EventsSerializer(last_event, context={'request': request})
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

            return Response({"message": "Atleta(s) adicionado(a)(s) a este evento!"}, status=status.HTTP_200_OK)
        except Athlete.DoesNotExist:
            return Response({"error": "Um erro ocurreu ao adicionar este(s) Atleta(s)!"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=["post"], url_path="delete_athlete", serializer_class=serializers.DeleteAthleteSerializer)
    def delete_athlete(self, request, pk=None):
        event = self.get_object()
        serializer = serializers.DeleteAthleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        athlete_id = serializer.validated_data["athlete_id"]

        try:
            athlete = Athlete.objects.get(id=athlete_id)
            event.individuals.remove(athlete)

            return Response({"message": "Atleta(s) removido(a)(s) deste evento!"}, status=status.HTTP_200_OK)
        except Athlete.DoesNotExist:
            return Response({"error": "Um erro ocurreu ao remover este(s) Atleta(s)!"}, status=status.HTTP_404_NOT_FOUND)
        
        
    @action(detail=True, methods=["get"], url_path="check_event_rate", permission_classes=[IsAuthenticated])
    def check_event_rate(self, request, pk=None):
        event = self.get_object()
        if not event.has_ended:
            return Response({
                "status": "error",
                "code": "event_not_ended",
                "message": "Este Evento ainda não foi realizado."
            }, status=status.HTTP_200_OK)
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
            event_ratings = DojosRatingAudit.objects.filter(event=event)
            if event_ratings.exists():
                ratings = [event.rating for event in event_ratings]
                ratings = ratings.append(rating)
            else:
                ratings = [rating]
            mean_rating = statistics.mean(ratings)
            event.rating = mean_rating
            event.save()
            DojosRatingAudit.objects.create(dojo=request.user, event=event, rating=rating)
            return Response({"message": "Obrigado pela sua opinião!"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": "Um erro ocurreu ao avaliar este Evento!", "message": e}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=["get"], url_path="export_athletes_excel", permission_classes=[IsAdminRoleorHigherForGET])
    def export_athletes_excel(self, request, pk=None):
        event = self.get_object()
        disciplines = event.disciplines.all()
        age_method = config('AGE_CALC_REF')

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Athletes"

        # Headers (add what you need)
        headers = ["Dojo", "Nome", "Idade", f"Nº {config('MAIN_ADMIN')}", "Género"]

        if list(disciplines) != []:
            headers.append("Modalidade")

        if event.has_categories:
            headers.append("Escalão")

        if not event.encounter:
            headers.append("Dorsal")

        ws.append(headers)

        if list(disciplines) == []:
            ws.append([
                    getattr(athlete.dojo, "username", ""),
                    getattr(athlete, "first_name", "") + getattr(athlete, "last_name", ""),
                    event_age,
                    getattr(athlete, "id_number", ""),
                    getattr(athlete, "gender", ""),
                ])
            
        else:

            all_members = []
            # Loop disciplines -> individuals
            for discipline in disciplines:

                for athlete in discipline.individuals.select_related("dojo").all():
                    season = event.season.split("/")[0]
                    event_age = get_comp_age(athlete.birth_date) if age_method == "true" else calc_age(age_method, athlete.birth_date, season)
                    category_to_assign = None

                    if not event.has_categories:
                    
                        ws.append([
                        getattr(athlete.dojo, "username", ""),
                        getattr(athlete, "first_name", "") + getattr(athlete, "last_name", ""),
                        event_age,
                        getattr(athlete, "id_number", ""),
                        getattr(athlete, "gender", ""),
                        discipline.name,
                    ])
                    
                    else:
                        categories = discipline.categories.filter(gender=athlete.gender, 
                                                            min_age__lte=event_age, 
                                                            max_age__gte=event_age
                                                            )
                        for category in categories:
                                
                            # Weights
                            if category.min_weight is None and category.max_weight is None:  # category does not have any weight limit
                                category_to_assign = category
                                
                            if category.min_weight is not None and category.max_weight is not None:
                                if category.min_weight <= athlete.weight <= category.max_weight:
                                    category_to_assign = category
                                else:
                                    continue
                            if category.max_weight is not None:
                                if athlete.weight < category.max_weight:
                                    category_to_assign = category
                            if category.min_weight is not None:
                                if athlete.weight >= category.min_weight:
                                    category_to_assign = category

                        all_members.append((discipline, athlete, event_age, category_to_assign))

            all_members_sorted = sorted(
                all_members,
                key=lambda x: (
                    getattr(x[1].dojo, "username", "").lower(),
                    getattr(x[1], "first_name", "").lower(),
                ),
            )

            name = ""
            dojo = ""
            i = 0

            for discipline, athlete, event_age, category_to_assign in all_members_sorted: 

                if name == getattr(athlete, "first_name", "") + getattr(athlete, "last_name", "") and dojo == getattr(athlete.dojo, "username", ""):
                    member_event_number = str(i).zfill(3)
                else:
                    i += 1
                    member_event_number = str(i).zfill(3)
                    name = getattr(athlete, "first_name", "") + getattr(athlete, "last_name", ""),
                    dojo = getattr(athlete.dojo, "username", ""),

                ws.append([
                    getattr(athlete.dojo, "username", ""),
                    getattr(athlete, "first_name", "") + getattr(athlete, "last_name", ""),
                    event_age,
                    getattr(athlete, "id_number", ""),
                    getattr(athlete, "gender", ""),
                    discipline.name,
                    category_to_assign.name,
                    member_event_number
                ])

        # Prepare response
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = (
            f'attachment; filename="event_{event.id}_athletes.xlsx"'
        )
        wb.save(response)

        return response
        

class DisciplineViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    queryset=Discipline.objects.all()
    serializer_class=serializers.DisciplinesSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = DisciplinesFilters

    serializer_classes = {
        "create": serializers.CreateDisciplineSerializer,
        "update": serializers.UpdateDisciplineSerializer
    }

    # def get_serializer_context(self):
    #     # extend context with request (already included by default in DRF)
    #     context = super().get_serializer_context()
    #     return context

    @action(detail=True, methods=["post"], url_path="add_athlete", serializer_class=serializers.AddDisciplineAthleteSerializer, permission_classes=[IsAuthenticated])
    def add_athlete(self, request, pk=None):
        age_method = config('AGE_CALC_REF')
        discipline = self.get_object()
        serializer = serializers.AddDisciplineAthleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        athlete_id = serializer.validated_data["athlete_id"]
        # will be used to check the season events is taking place in
        event_id = serializer.validated_data["event_id"]

        try:
            athlete = Athlete.objects.get(id=athlete_id)
            event = Event.objects.get(id=event_id)
            season = event.season.split("/")[0]
            event_age = get_comp_age(athlete.birth_date) if age_method == "true" else calc_age(age_method, athlete.birth_date, season)

            if not event.has_categories:
                discipline.individuals.add(athlete)
                return Response({"message": "Atleta(s) adicionado(a)(s) a esta Modalidade"}, status=status.HTTP_200_OK)
            
            categories = discipline.categories.filter(gender=athlete.gender, 
                                                      min_age__lte=event_age, 
                                                      max_age__gte=event_age
                                                      )

            if list(categories) == []:
                return Response({"error": "Não existem Escalões que satisfaçam este(a)(s) Atleta(s)"}, status=status.HTTP_400_BAD_REQUEST)

            for category in categories:

                min_grad = float(category.min_grad) if category.min_grad is not None and category.min_grad != "" else None
                max_grad = float(category.max_grad) if category.max_grad is not None and category.max_grad != "" else None
                grad = float(athlete.graduation) if athlete.graduation is not None and athlete.graduation != "" else None

                # Graduations
                if min_grad is None and max_grad is None:
                    pass
                if min_grad is not None and max_grad is not None:
                    if min_grad > grad > max_grad:
                        pass
                    else:
                        return Response({"error": "Graduação não está dentro dos limites estipulados para o Escalão"}, status=status.HTTP_400_BAD_REQUEST)
                if max_grad is not None:
                    if grad < max_grad:
                        return Response({"error": "Graduação máxima para este Escalão não respeitada"}, status=status.HTTP_400_BAD_REQUEST)
                if min_grad is not None:
                    if grad > min_grad:
                        return Response({"error": "Graduação mínima para este Escalão não respeitada"}, status=status.HTTP_400_BAD_REQUEST)
                    
                # Weights
                if category.min_weight is None and category.max_weight is None:  # category does not have any weight limit
                    discipline.individuals.add(athlete)
                else:
                    if athlete.weight is None:
                        return Response({"status": "info", 
                                         "message": "O escalão disponível para este Atleta pede que adicione um peso."}, 
                                         status=status.HTTP_200_OK)
                    

                if category.min_weight is not None and category.max_weight is not None:
                    if category.min_weight <= athlete.weight <= category.max_weight:
                         discipline.individuals.add(athlete)
                    else:
                        continue
                if category.max_weight is not None:
                    if athlete.weight < category.max_weight:
                        discipline.individuals.add(athlete)
                if category.min_weight is not None:
                    if athlete.weight >= category.min_weight:
                        discipline.individuals.add(athlete)
                
            # if not success:
            #     return Response({"error": "Idade do Atleta não permite inscrever nos Escalões disponíveis"}, status=status.HTTP_400_BAD_REQUEST)

            return Response({"message": "Atleta(s) adicionado(a)(s) a esta Modalidade"}, status=status.HTTP_200_OK)
        except Athlete.DoesNotExist:
            return Response({"error": "Um erro ocurreu ao adicionar este(s) Atleta(s)"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=["post"], url_path="delete_athlete", serializer_class=serializers.DeleteAthleteSerializer)
    def delete_athlete(self, request, pk=None):
        discipline = self.get_object()
        serializer = serializers.DeleteAthleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        athlete_id = serializer.validated_data["athlete_id"]

        try:
            athlete = Athlete.objects.get(id=athlete_id)
            discipline.individuals.remove(athlete)

            return Response({"message": "Atleta removido desta Modalidade"}, status=status.HTTP_200_OK)
        except Athlete.DoesNotExist:
            return Response({"error": "Um erro ocurreu ao remover este Atleta"}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=["post"], url_path="add_team", serializer_class=serializers.AddTeamSerializer)
    def add_team(self, request):
        discipline = self.get_object()
        serializer = serializers.AddTeamSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        team_id = serializer.validated_data["team_id"]

        try:
            team = Team.objects.get(id=team_id)
            discipline.teams.add(team)

            return Response({"message": "Equipa adicionada a esta Modalidade!"}, status=status.HTTP_200_OK)
        except Athlete.DoesNotExist:
            return Response({"error": "Um erro ocurreu ao adicionar esta Equipa!"}, status=status.HTTP_404_NOT_FOUND)


    @action(detail=True, methods=["post"], url_path="delete_team", serializer_class=serializers.AddTeamSerializer)
    def delete_team(self, request, pk=None):
        discipline = self.get_object()
        serializer = serializers.AddTeamSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        team_id = serializer.validated_data["team_id"]

        try:
            team = Team.objects.get(id=team_id)
            discipline.teams.remove(team)

            return Response({"message": "Equipa removida desta Modalidade"}, status=status.HTTP_200_OK)
        except Athlete.DoesNotExist:
            return Response({"error": "Um erro ocurreu ao remover esta Equipa"}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=["post"], url_path="add_category", serializer_class=serializers.AddCategorySerializer, permission_classes=[IsAuthenticated])
    def add_category(self, request, pk=None):
        event = self.get_object()
        serializer = serializers.AddCategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category_id = serializer.validated_data["category_id"]

        try:
            category = Category.objects.get(id=category_id)
            event.categories.add(category)

            return Response({"message": "Escalão(ões) adicionado(s) a esta modalidade"}, status=status.HTTP_200_OK)
        except Category.DoesNotExist:
            return Response({"error": "Um erro ocurreu ao adicionar este Escalão"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=["post"], url_path="delete_category", serializer_class=serializers.AddCategorySerializer, permission_classes=[IsAuthenticated])
    def delete_category(self, request, pk=None):
        event = self.get_object()
        serializer = serializers.AddCategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category_id = serializer.validated_data["category_id"]

        try:
            category = Category.objects.get(id=category_id)
            event.categories.remove(category)

            return Response({"message": "Escalão(ões) removido(s) desta modalidade"}, status=status.HTTP_200_OK)
        except Category.DoesNotExist:
            return Response({"error": "Um erro ocurreu ao remover este Escalão"}, status=status.HTTP_404_NOT_FOUND)
        

class DojosViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    queryset=Dojo.objects.all()
    serializer_class=serializers.DojosSerializer
    permission_classes = [IsGETforClubs]

    serializer_classes = {
        "create": serializers.CreateDojosSerializer,
    }

    def perform_create(self, serializer):
        user = self.request.user
        if user.role != "main_admin":
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer.save(mother_acount=user)
    

@api_view(['GET'])
# @authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated, IsPayingUserorAdminForGet])
def notifications(request):
    notifications = Notification.objects.filter(dojo=request.user)
    serializer = serializers.NotificationsSerializer(notifications, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminRoleorHigher])
def dojos_athletes(request):
    data = User.objects.exclude(role__in=["main_admin", "superuser"])\
                        .annotate(athlete_count=Count('athlete'))\
                        .values('username', 'athlete_count')
    return Response(data)
    

class NotificationViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    queryset=Notification.objects.all()
    serializer_class=serializers.NotificationsSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsNationalForPostDelete]
    filter_backends = [DjangoFilterBackend]
    filterset_class = NotificationsFilters

    # serializer_classes = {
    #     "create": serializers.CreateEventSerializer,
    #     "update": serializers.UpdateEventSerializer
    # }

    def get_queryset(self):
        user = self.request.user
        if getattr(user, "role", None) in ["main_admin", "superuser"]:
            return Notification.objects.all().order_by("created_at")
        return Notification.objects.filter(dojo=user) .order_by("created_at")


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
