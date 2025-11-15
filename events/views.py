from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count
from django.utils import timezone
from django.http import HttpResponse
from django.db.models import Q
from decouple import config
import statistics
from datetime import timedelta, datetime
import openpyxl

from .filters import DisciplinesFilters
from clubs.models import ClubRatingAudit
from .models import Event, Discipline, Announcement
from registration.models import Member, Team
from core.permissions import IsAuthenticatedOrReadOnly, EventIndividualsPermission, EventPermission, IsAdminRoleorHigherForGET, IsAdminRoleorHigher
from core.models import Category
from events import serializers
from clubs.serializers import RatingSerializer
from core.utils.utils import calc_age
from registration.utils.utils import get_comp_age
from core.views import MultipleSerializersMixIn

from rest_framework import viewsets, filters, status
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework. views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, action
from drf_spectacular.utils import extend_schema

# Create your views here.

class EventViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    queryset=Event.objects.all()
    serializer_class=serializers.EventsSerializer
    permission_classes = [EventPermission]

    serializer_classes = {
        "create": serializers.CreateEventSerializer,
        "update": serializers.UpdateEventSerializer
    }

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        if getattr(user, "role", None) == "free_club":
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
    
    @action(detail=True, 
            methods=["post"], 
            url_path="add_athlete", 
            serializer_class=serializers.AddAthleteSerializer, 
            permission_classes=[EventIndividualsPermission])
    def add_athlete(self, request, pk=None):
        event = self.get_object()
        serializer = serializers.AddAthleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member_id = serializer.validated_data["member_id"]

        try:
            athlete = Member.objects.get(id=member_id)
            event.individuals.add(athlete)

            return Response({"message": "Atleta(s) adicionado(a)(s) a este evento!"}, status=status.HTTP_200_OK)
        except Member.DoesNotExist:
            return Response({"error": "Um erro ocurreu ao adicionar este(s) Atleta(s)!"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, 
            methods=["post"], 
            url_path="delete_athlete", 
            serializer_class=serializers.DeleteAthleteSerializer, 
            permission_classes=[EventIndividualsPermission])
    def delete_athlete(self, request, pk=None):
        event = self.get_object()
        serializer = serializers.DeleteAthleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member_id = serializer.validated_data["member_id"]

        try:
            athlete = Member.objects.get(id=member_id)
            event.individuals.remove(athlete)

            return Response({"message": "Atleta(s) removido(a)(s) deste evento!"}, status=status.HTTP_200_OK)
        except Member.DoesNotExist:
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
        if ClubRatingAudit.objects.filter(club=request.user, event=event).exists():
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
    
    @action(detail=False, methods=["post"], url_path="events_days_per_month", permission_classes=[IsAuthenticated], serializer_class=serializers.EventDaysSerializer)
    def events_days_per_month(self, request, pk=None):
        serializer = serializers.EventDaysSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        month = serializer.validated_data["month"]
        if not month:
            return Response({'error': 'Month parameter is required, e.g., "2025-11".'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Parse the provided month string
            date_obj = datetime.strptime(month, "%Y-%m")
        except ValueError:
            return Response({'error': 'Invalid month format. Use "YYYY-MM".'}, status=status.HTTP_400_BAD_REQUEST)

        # Filter events in that month
        events = Event.objects.filter(
            event_date__year=date_obj.year,
            event_date__month=date_obj.month
        )

        serializer = serializers.CompactEventsSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="rate_event", serializer_class=RatingSerializer)
    def rate_event(self, request, pk=None):
        event = self.get_object()
        serializer = RatingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rating = serializer.validated_data["rating_signal"]
        try:
            event_ratings = ClubRatingAudit.objects.filter(event=event)
            if event_ratings.exists():
                ratings = [event.rating for event in event_ratings]
                ratings = ratings.append(rating)
            else:
                ratings = [rating]
            mean_rating = statistics.mean(ratings)
            event.rating = mean_rating
            event.save()
            ClubRatingAudit.objects.create(club=request.user, event=event, rating=rating)
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
                    getattr(athlete.club, "username", ""),
                    getattr(athlete, "first_name", "") + getattr(athlete, "last_name", ""),
                    event_age,
                    getattr(athlete, "id_number", ""),
                    getattr(athlete, "gender", ""),
                ])
            
        else:

            all_members = []
            # Loop disciplines -> individuals
            for discipline in disciplines:

                for athlete in discipline.individuals.select_related("club").all():
                    season = event.season.split("/")[0]
                    event_age = get_comp_age(athlete.birth_date) if age_method == "true" else calc_age(age_method, athlete.birth_date, season)
                    category_to_assign = None

                    if not event.has_categories:
                    
                        ws.append([
                        getattr(athlete.club, "username", ""),
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
                    getattr(x[1].club, "username", "").lower(),
                    getattr(x[1], "first_name", "").lower(),
                    getattr(x[1], "last_name", "").lower(),
                ),
            )

            name = ""
            club = ""
            i = 0

            for discipline, athlete, event_age, category_to_assign in all_members_sorted:

                curr_name = getattr(athlete, "first_name", "") + getattr(athlete, "last_name", "")
                curr_club = getattr(athlete.club, "username", "")

                if curr_name == name and curr_club == club:
                    # Same athlete as previous → repeat the same number
                    member_event_number = str(i).zfill(3)
                else:
                    # New athlete → increment and assign new number
                    i += 1
                    member_event_number = str(i).zfill(3)
                    name = curr_name
                    club = curr_club

                
                new_category_to_assign = ""
                if category_to_assign != None:
                    if category_to_assign.max_weight != None:
                        new_category_to_assign = f"{category_to_assign.name} - {category_to_assign.max_weight}"
                    elif category_to_assign.min_weight != None:
                        new_category_to_assign = f"{category_to_assign.name} + {category_to_assign.min_weight}"

                ws.append([
                    getattr(athlete.club, "username", ""),
                    getattr(athlete, "first_name", "") + " " + getattr(athlete, "last_name", ""),
                    event_age,
                    getattr(athlete, "id_number", ""),
                    getattr(athlete, "gender", ""),
                    discipline.name,
                    new_category_to_assign,
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
    queryset=Discipline.objects.all().order_by("name")
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
        member_id = serializer.validated_data["member_id"]
        # will be used to check the season events is taking place in
        event_id = serializer.validated_data["event_id"]

        try:
            athlete = Member.objects.get(id=member_id)
            event = Event.objects.get(id=event_id)
            season = event.season.split("/")[0]
            event_age = get_comp_age(athlete.birth_date) if age_method == "true" else calc_age(age_method, athlete.birth_date, season)

            if not event.has_categories:
                discipline.individuals.add(athlete)
                return Response({"message": "Membro(s) adicionado(s) a esta Modalidade"}, status=status.HTTP_200_OK)

            # if targeted discipline has no categories, it is assumed that anyone can be registered
            if discipline.categories.count() == 0:
                # TODO: quick fix for coaches only allow more than 1º Dan
                if float(athlete.graduation) > 6:
                    return Response({"error": "Treinadores têm de ter graduação superior a 1º Dan!"}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    discipline.individuals.add(athlete)
                    return Response({"message": "Treinador(es) adicionado(s) a este Evento"}, status=status.HTTP_200_OK)
            
            categories = discipline.categories.filter(gender=athlete.gender, 
                                                      min_age__lte=event_age, 
                                                      max_age__gte=event_age
                                                      )

            if list(categories) == []:
                return Response({"error": "Não existem Escalões que satisfaçam este(s) Membro(s)"}, status=status.HTTP_400_BAD_REQUEST)

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

            return Response({"message": "Membro(s) adicionado(s) a esta Modalidade"}, status=status.HTTP_200_OK)
        except Member.DoesNotExist:
            return Response({"error": "Um erro ocurreu ao adicionar este(s) Membro(s)"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=["post"], url_path="delete_athlete", serializer_class=serializers.DeleteAthleteSerializer)
    def delete_athlete(self, request, pk=None):
        discipline = self.get_object()
        serializer = serializers.DeleteAthleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member_id = serializer.validated_data["member_id"]

        try:
            athlete = Member.objects.get(id=member_id)
            discipline.individuals.remove(athlete)

            return Response({"message": "Atleta removido desta Modalidade"}, status=status.HTTP_200_OK)
        except Member.DoesNotExist:
            return Response({"error": "Um erro ocurreu ao remover este Atleta"}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['delete'], url_path="delete_all_individuals")
    def delete_all_individuals(self, request, pk=None):
        try:
            discipline = self.get_object()
            individuals_count = discipline.individuals.count()
            discipline.individuals.clear()
            if individuals_count <= 1:
                return Response(
                    {"message": f'Atleta removido de {discipline.name}'},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"message": f"Removidos {individuals_count} Atletas de {discipline.name}"},
                    status=status.HTTP_200_OK
                )
        except Discipline.DoesNotExist:
            return Response(
                    {"error": "Ocorreu um erro a remover estes Atletas. Tente mais tarde ou contacte o administrador."},
                    status=status.HTTP_200_OK
                )
    
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
        except Member.DoesNotExist:
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
        except Member.DoesNotExist:
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
        

class ActiveAnnouncementView(APIView):
    @extend_schema(description="Returns a list of currently active annoucements")
    @permission_classes(IsAuthenticatedOrReadOnly)
    def get(self, request):
        announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')

        if not announcements.exists():
            return Response(None)

        serializer = serializers.AnnouncementSerializer(announcements, many=True)
        return Response(serializer.data)
    
 # return Response({
            #     "id": announcement.id,
            #     "message": announcement.message,
            #     "created_at": announcement.created_at,
            # })
