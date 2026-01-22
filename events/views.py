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

from .filters import DisciplinesFilters, EventsFilters
from clubs.models import ClubRatingAudit
from .models import Event, Discipline, Announcement, DisciplineMember
from registration.models import Member, Team
from core.permissions import IsAuthenticatedOrReadOnly, EventIndividualsPermission, EventPermission, IsAdminRoleorHigherForGET, IsAdminRoleorHigher
from core.models import Category
from events import serializers
from registration import serializers as registrationSerializers
from clubs.serializers import RatingSerializer
from core.utils.utils import calc_age
from registration.utils.utils import get_comp_age, athlete_age
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
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ["name", "event_date", "start_registration"]
    filterset_class = EventsFilters

    serializer_classes = {
        "list": serializers.CompactEventsSerializer,
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
        serializer = serializers.CompactEventsSerializer(next_event, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=["get"], url_path="last_event")
    def last_event(self, request):
        last_event = Event.objects.filter(has_ended=True).order_by('event_date').last()
        if last_event is None:
            return Response([])
        serializer = serializers.CompactEventsSerializer(last_event, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, 
            methods=["post"], 
            url_path="add_member", 
            serializer_class=serializers.AddMemberSerializer, 
            permission_classes=[EventIndividualsPermission])
    def add_member(self, request, pk=None):
        event = self.get_object()
        serializer = serializers.AddMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member_id = serializer.validated_data["member_id"]

        try:
            member = Member.objects.get(id=member_id)
            event.individuals.add(member)

            return Response({"message": "Atleta(s) adicionado(a)(s) a este evento!"}, status=status.HTTP_200_OK)
        except Member.DoesNotExist:
            return Response({"error": "Ocorreu um erro ao adicionar este(s) Atleta(s)!"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, 
            methods=["post"], 
            url_path="delete_member", 
            serializer_class=serializers.DeleteMemberSerializer, 
            permission_classes=[EventIndividualsPermission])
    def delete_member(self, request, pk=None):
        event = self.get_object()
        serializer = serializers.DeleteMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member_id = serializer.validated_data["member_id"]

        try:
            member = Member.objects.get(id=member_id)
            event.individuals.remove(member)

            return Response({"message": "Atleta(s) removido(a)(s) deste evento!"}, status=status.HTTP_200_OK)
        except Member.DoesNotExist:
            return Response({"error": "Ocorreu um erro ao remover este(s) Atleta(s)!"}, status=status.HTTP_404_NOT_FOUND)
        
        
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
    
    @action(
        detail=False,
        methods=["get"],
        url_path="events_days_per_month",
        permission_classes=[IsAuthenticated],
    )
    def events_days_per_month(self, request):
        month = request.query_params.get("month")
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
        days = []
        for event in events:
            days.append(event.event_date.day)
        serializer = serializers.CompactEventsSerializer(events, many=True)
        return Response({"days": sorted(days), "results": serializer.data}, status=200)

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
            return Response({"error": "Ocorreu um erro ao avaliar este Evento!", "message": e}, status=status.HTTP_400_BAD_REQUEST)
    

    @action(detail=True, methods=["get"], url_path="export_members_excel", permission_classes=[IsAdminRoleorHigherForGET])
    def export_members_excel(self, request, pk=None):
        event = self.get_object()
        disciplines = event.disciplines.all()
        age_method = config('AGE_CALC_REF')

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Members"

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
                    getattr(member.club, "username", ""),
                    getattr(member, "first_name", "") + getattr(member, "last_name", ""),
                    event_age,
                    getattr(member, "id_number", ""),
                    getattr(member, "gender", ""),
                ])
            
        else:

            all_members = []
            # Loop disciplines -> individuals
            for discipline in disciplines:

                for member in discipline.individuals.select_related("club").all():
                    season = event.season.split("/")[0]
                    event_age = get_comp_age(member.birth_date) if age_method == "true" else calc_age(age_method, member.birth_date, season)
                    category_to_assign = None

                    if not event.has_categories:
                    
                        ws.append([
                        getattr(member.club, "username", ""),
                        getattr(member, "first_name", "") + getattr(member, "last_name", ""),
                        event_age,
                        getattr(member, "id_number", ""),
                        getattr(member, "gender", ""),
                        discipline.name,
                    ])
                    
                    else:
                        categories = discipline.categories.filter(gender=member.gender, 
                                                            min_age__lte=event_age, 
                                                            max_age__gte=event_age
                                                            )
                        for category in categories:
                                
                            # Weights
                            if category.min_weight is None and category.max_weight is None:  # category does not have any weight limit
                                category_to_assign = category
                                
                            if category.min_weight is not None and category.max_weight is not None:
                                if category.min_weight <= member.weight <= category.max_weight:
                                    category_to_assign = category
                                else:
                                    continue
                            if category.max_weight is not None:
                                if member.weight < category.max_weight:
                                    category_to_assign = category
                            if category.min_weight is not None:
                                if member.weight >= category.min_weight:
                                    category_to_assign = category

                        all_members.append((discipline, member, event_age, category_to_assign))

            all_members_sorted = sorted(
                all_members,
                key=lambda x: (
                    getattr(x[1].club, "username", "").lower(),
                    getattr(x[1], "first_name", "").lower(),
                ),
            )

            name = ""
            club = ""
            i = 0

            for discipline, member, event_age, category_to_assign in all_members_sorted: 

                if name == getattr(member, "first_name", "") + getattr(member, "last_name", "") and club == getattr(member.club, "username", ""):
                    member_event_number = str(i).zfill(3)
                else:
                    i += 1
                    member_event_number = str(i).zfill(3)
                    name = getattr(member, "first_name", "") + getattr(member, "last_name", ""),
                    club = getattr(member.club, "username", ""),

                ws.append([
                    getattr(member.club, "username", ""),
                    getattr(member, "first_name", "") + getattr(member, "last_name", ""),
                    event_age,
                    getattr(member, "id_number", ""),
                    getattr(member, "gender", ""),
                    discipline.name,
                    category_to_assign.name,
                    member_event_number
                ])

        # Prepare response
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = (
            f'attachment; filename="event_{event.id}_members.xlsx"'
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

    @action(detail=True, methods=["post"], url_path="add_member", serializer_class=serializers.AddDisciplineMemberSerializer, permission_classes=[IsAuthenticated])
    def add_member(self, request, pk=None):
        age_method = config('AGE_CALC_REF')
        discipline = self.get_object()
        serializer = serializers.AddDisciplineMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member_id = serializer.validated_data["member_id"]
        # will be used to check the season events is taking place in
        event_id = serializer.validated_data["event_id"]

        try:
            member = Member.objects.get(id=member_id)
            event = Event.objects.get(id=event_id)
            season = event.season.split("/")[0]
            event_age = get_comp_age(member.birth_date) if age_method == "true" else calc_age(age_method, member.birth_date, season)

            if not event.has_categories:
                discipline.add_member(member)
                return Response({"message": "Membro(s) adicionado(s) a esta Modalidade."}, status=status.HTTP_200_OK)

            # if targeted discipline has no categories, it is assumed that anyone can be registered
            if discipline.categories.count() == 0:
                # TODO: quick fix for coaches only allow more than 1º Dan
                if float(member.graduation) > 6:
                    return Response({"error": "Treinadores têm de ter graduação superior a 1º Dan!"}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    discipline.add_member(member)
                    return Response({"message": "Treinador(es) adicionado(s) a este Evento."}, status=status.HTTP_200_OK)
            
            categories = discipline.categories.filter(gender=member.gender, 
                                                      min_age__lte=event_age, 
                                                      max_age__gte=event_age
                                                      )

            if list(categories) == []:
                return Response({"error": "Não existem Escalões que satisfaçam este(s) Membro(s)."}, status=status.HTTP_400_BAD_REQUEST)

            for category in categories:

                min_grad = float(category.min_grad) if category.min_grad is not None and category.min_grad != "" else None
                max_grad = float(category.max_grad) if category.max_grad is not None and category.max_grad != "" else None
                grad = float(member.graduation) if member.graduation is not None and member.graduation != "" else None

                # Graduations
                if min_grad is None and max_grad is None:
                    pass
                if min_grad is not None and max_grad is not None:
                    if min_grad > grad > max_grad:
                        pass
                    else:
                        return Response({"error": "Graduação não está dentro dos limites estipulados para o Escalão."}, status=status.HTTP_400_BAD_REQUEST)
                if max_grad is not None:
                    if grad < max_grad:
                        return Response({"error": "Graduação máxima para este Escalão não respeitada."}, status=status.HTTP_400_BAD_REQUEST)
                if min_grad is not None:
                    if grad > min_grad:
                        return Response({"error": "Graduação mínima para este Escalão não respeitada."}, status=status.HTTP_400_BAD_REQUEST)
                    
                # Weights
                if category.min_weight is None and category.max_weight is None:  # category does not have any weight limit
                    discipline.add_member(member)
                else:
                    if member.weight is None:
                        return Response({"status": "info", 
                                         "message": "O escalão disponível para este Atleta pede que adicione um peso."}, 
                                         status=status.HTTP_200_OK)
                    

                if category.min_weight is not None and category.max_weight is not None:
                    if category.min_weight <= member.weight <= category.max_weight:
                         discipline.add_member(member)
                    else:
                        continue
                if category.max_weight is not None:
                    if member.weight < category.max_weight:
                        discipline.add_member(member)
                if category.min_weight is not None:
                    if member.weight >= category.min_weight:
                        discipline.add_member(member)
                
            # if not success:
            #     return Response({"error": "Idade do Atleta não permite inscrever nos Escalões disponíveis"}, status=status.HTTP_400_BAD_REQUEST)

            return Response({"message": "Membro(s) adicionado(s) a esta Modalidade."}, status=status.HTTP_200_OK)
        except Member.DoesNotExist:
            return Response({"error": "Ocorreu um erro ao adicionar este(s) Membro(s)."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=["post"], url_path="delete_member", serializer_class=serializers.DeleteMemberSerializer)
    def delete_member(self, request, pk=None):
        discipline = self.get_object()
        serializer = serializers.DeleteMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member_id = serializer.validated_data["member_id"]

        try:
            member = Member.objects.get(id=member_id)
            discipline.individuals.remove(member)

            if discipline.is_coach:
                return Response({"message": "Treinador removido."}, status=status.HTTP_200_OK)
            else:
                return Response({"message": f"Atleta removido de {discipline.name}."}, status=status.HTTP_200_OK)
        except Member.DoesNotExist:
            return Response({"error": "Ocorreu um erro ao remover este Atleta."}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['delete'], url_path="delete_all_individuals")
    def delete_all_individuals(self, request, pk=None):
        try:
            discipline = self.get_object()
        except Discipline.DoesNotExist:
            return Response(
                    {"error": "Ocorreu um erro a remover estes Atletas. Tente mais tarde ou contacte o administrador."},
                    status=status.HTTP_200_OK
                )
        try:
            individuals_count = discipline.individuals.filter(club=request.user).count()
            DisciplineMember.objects.filter(
                discipline=discipline,
                member__club=request.user
            ).delete()
        except Member.DoesNotExist:
            return Response({"error": "Ocorreu um erro ao remover todos os Atletas desta Modalidade."}, status=status.HTTP_404_NOT_FOUND)
        
        if individuals_count <= 1:
            message = f'Atleta removido de {discipline.name}.' if not discipline.is_coach else 'Treinador removido.'
            return Response(
                {"message": message},
                status=status.HTTP_200_OK
            )
        else:
            message = f"Removidos {individuals_count} Atletas de {discipline.name}." if not discipline.is_coach else f'Removidos {individuals_count} Treinadores.'
            return Response(
                {"message": message},
                status=status.HTTP_200_OK
            )
    
    @action(detail=True, methods=["post"], url_path="add_team", serializer_class=registrationSerializers.CreateTeamSerializer)
    def add_team(self, request, pk=None):
        serializer = registrationSerializers.CreateTeamSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        chosen_category = serializer.validated_data.pop("chosen_category", None)

        last_team = Team.objects.filter(club=self.request.user).order_by("team_number").last()
        team_number = (last_team.team_number if last_team else 0) + 1

        discipline = self.get_object()
        age_method = config('AGE_CALC_REF')
        event = discipline.event

        try:
            season = event.season.split("/")[0]
            members = [
                serializer.validated_data["athlete1"],
                serializer.validated_data["athlete2"],
                serializer.validated_data["athlete3"]
                ]
            
            members = [a for a in members if a != ""]

            member_ages = {
                member.id: athlete_age(member, age_method, season) for member in members
            }

            # the athlete with largest age will determine the category age
            oldest_member_id, max_member_age = max(
                member_ages.items(),
                key=lambda item: item[1]
            )

            if chosen_category is not None and chosen_category != "":
                categories = discipline.categories.filter(id=chosen_category)

            else:
                categories = discipline.categories.filter(gender=serializer.validated_data["gender"], 
                                                      min_age__lte=max_member_age, 
                                                      max_age__gte=max_member_age
                                                      )
            
            if list(categories) == []:
                return Response({"error": "Não existem Escalões que satisfaçam este(s) Membro(s) para o Género selecionado."
                "."}, status=status.HTTP_400_BAD_REQUEST)
            
            if len(list(categories)) > 1:
                return Response({
                    "status": "info", 
                    "message": "Existe mais que um Escalão possível para inscrever esta equipa. Selecione apenas um.",
                    "category_ids": categories.values_list("id", flat=True)}, 
                    status=status.HTTP_200_OK)
            
            base_category = categories.get()

            if base_category.max_athletes is not None and base_category.max_athletes != len(members):
                return Response({"error": f"Escalão determinado obriga a {base_category.max_athletes} Atletas, enviou {len(members)}."}, status=status.HTTP_400_BAD_REQUEST)
            
            lower_category = (
                discipline.categories
                .filter(
                    gender=base_category.gender,
                    max_age__lt=base_category.min_age
                )
                .order_by("-max_age")
                .first()
            )
            
            outside_base = []
            for member in members: 
                
                age = athlete_age(member, age_method, season) 
                
                if base_category.min_age <= age <= base_category.max_age: 
                    pass 
                else: 
                    if lower_category is not None: 
                        if lower_category.min_age <= age <= lower_category.max_age: 
                            outside_base.append(member) 
                        else: 
                            return Response(
                                {
                                    "error": "Um dos Atletas é mais novo que o permitido para o Escalão determinado para esta Equipa."
                                }, 
                                status=status.HTTP_400_BAD_REQUEST
                            )

                    if len(outside_base) > 1:
                        return Response(
                            {
                                "error": "Apenas um dos Atletas pode ser promovido do Escalão imediatamente inferior àquele determinado para esta Equipa."
                            }, 
                            status=status.HTTP_400_BAD_REQUEST
                        )
            
                min_grad = float(base_category.min_grad) if base_category.min_grad is not None and base_category.min_grad != "" else None
                max_grad = float(base_category.max_grad) if base_category.max_grad is not None and base_category.max_grad != "" else None
                grad = float(member.graduation) if member.graduation is not None and member.graduation != "" else None

                # Graduations
                if min_grad is not None and max_grad is not None:
                    if not min_grad > grad > max_grad:
                        return Response({"error": "Graduação não está dentro dos limites estipulados para o Escalão."}, status=status.HTTP_400_BAD_REQUEST)
                if max_grad is not None and grad < max_grad:
                    return Response({"error": "Graduação máxima para este Escalão não respeitada."}, status=status.HTTP_400_BAD_REQUEST)
                if min_grad is not None and grad > min_grad:
                    return Response({"error": "Graduação mínima para este Escalão não respeitada."}, status=status.HTTP_400_BAD_REQUEST)
                    
                # Weights
                if base_category.min_weight is None and base_category.max_weight is None:  # category does not have any weight limit
                    continue
                else:
                    if member.weight is None:
                        return Response({"status": "info", 
                                        "message": "O escalão disponível para este Atleta pede que adicione um peso."}, 
                                        status=status.HTTP_200_OK)
                    

                if base_category.min_weight is not None and base_category.max_weight is not None:
                    if base_category.min_weight <= member.weight <= base_category.max_weight:
                        continue
                    else:
                        return Response({"error": "Um dos Membros não tem o peso indicado para este Escalão."}, status=status.HTTP_400_BAD_REQUEST)
                if base_category.max_weight is not None:
                    if member.weight < base_category.max_weight:
                        continue
                    else:
                        return Response({"error": "Um dos Membros não tem o peso indicado para este Escalão."}, status=status.HTTP_400_BAD_REQUEST)
                if base_category.min_weight is not None:
                    if member.weight >= base_category.min_weight:
                        continue
                    else: 
                        return Response({"error": "Um dos Membros não tem o peso indicado para este Escalão."}, status=status.HTTP_400_BAD_REQUEST)

            created_team = Team.objects.create(**serializer.validated_data, 
                                               club=self.request.user, 
                                               team_number=team_number,
                                               category=base_category)
            discipline.add_team(created_team)

            return Response({"message": "Equipa adicionada a esta Modalidade!"}, status=status.HTTP_200_OK)
        except Member.DoesNotExist:
            return Response({"error": "Ocorreu um erro ao adicionar esta Equipa!"}, status=status.HTTP_404_NOT_FOUND)


    @action(detail=True, methods=["post"], url_path="delete_team", serializer_class=serializers.DeleteTeamSerializer)
    def delete_team(self, request, pk=None):
        serializer = serializers.DeleteTeamSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        team_id = serializer.validated_data["team_id"]

        try:
            team = Team.objects.get(id=team_id)
            team.delete()

            return Response({"message": "Equipa removida desta Modalidade."}, status=status.HTTP_200_OK)
        except Team.DoesNotExist:
            return Response({"error": "Ocorreu um erro ao remover esta Equipa."}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['delete'], url_path="delete_all_teams")
    def delete_all_teams(self, request, pk=None):
        try:
            discipline = self.get_object()
        except Discipline.DoesNotExist:
            return Response(
                    {"error": "Ocorreu um erro ao remover todos as Equipas desta Modalidade. Tente mais tarde ou contacte o administrador."},
                    status=status.HTTP_200_OK
                )
        
        try:
            teams_count = discipline.teams.filter(club=request.user).count()
            Team.objects.filter(club=request.user).delete()
        except Team.DoesNotExist:
            return Response({"error": "Ocorreu um erro ao remover todos as Equipas desta Modalidade. Tente mais tarde ou contacte o administrador."}, status=status.HTTP_404_NOT_FOUND)
        
        if teams_count <= 1:
            return Response(
                {"message": f'Equipa removida de {discipline.name}.'},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"message": f"Removidas {teams_count} Equipas de {discipline.name}."},
                status=status.HTTP_200_OK
            )
        
        
    @action(
        detail=True,
        methods=["patch"],
        url_path="add_categories",
        serializer_class=serializers.AddCategorySerializer,
        permission_classes=[IsAuthenticated],
    )
    def update_categories(self, request, pk=None):
        """
        Adiciona múltiplos Escalões (Categories) a uma Modalidade (Discipline) dentro de um Evento.

        - Recebe uma lista de IDs de Escalões
        - Adiciona todos numa única operação
        - Não remove Escalões já associados
        """
        event = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category_ids = serializer.validated_data["category_ids"]
        categories = Category.objects.filter(id__in=category_ids)
        
        if not categories.exists():
            return Response(
                {"error": "Nenhum Escalão válido foi encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        event.categories.add(*categories)
        return Response(
            {
                "message": "Escalão(ões) adicionados com sucesso.",
                "added_count": categories.count(),
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="delete_category", serializer_class=serializers.AddCategorySerializer, permission_classes=[IsAuthenticated])
    def delete_category(self, request, pk=None):
        event = self.get_object()
        serializer = serializers.AddCategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category_ids = serializer.validated_data["category_ids"]

        try:
            categories = Category.objects.filter(id__in=category_ids)
            for category in categories:
                event.categories.remove(category)

            return Response({"message": "Escalão(ões) removido(s) desta modalidade."}, status=status.HTTP_200_OK)
        except Category.DoesNotExist:
            return Response({"error": "Ocorreu um erro ao remover este Escalão."}, status=status.HTTP_404_NOT_FOUND)
        

class ActiveAnnouncementView(APIView):
    @extend_schema(description="Returns a list of currently active annoucements")
    @permission_classes(IsAuthenticatedOrReadOnly)
    def get(self, request):
        announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')

        if not announcements.exists():
            return Response([])

        serializer = serializers.AnnouncementSerializer(announcements, many=True)
        return Response(serializer.data)
    
 # return Response({
            #     "id": announcement.id,
            #     "message": announcement.message,
            #     "created_at": announcement.created_at,
            # })
