from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django_filters.rest_framework import DjangoFilterBackend

from .forms import AthleteForm, FilterAthleteForm, TeamForm, FilterTeamForm, TeamCategorySelection
from .models import Athlete, Team, Classification
from .filters import AthletesFilters
from .templatetags.team_extras import valid_athletes
from .utils.utils import check_athlete_data, get_comp_age, check_filter_data, check_match_type, check_teams_data, check_team_selection
from dojos.models import Event
import datetime
import json
import os

from rest_framework import viewsets, status
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.exceptions import PermissionDenied
import registration.serializers as serializers
import dojos.serializers as dojo_serializers

# views for the athlets registrations

class MultipleSerializersMixIn:
    serializer_classes = {}

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, self.serializer_class)


class AthletesViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    # TODO: order get request by the category_index from the serializer
    queryset=Athlete.objects.all()
    serializer_class = serializers.AthletesSerializer
    # authentication_classes = [SessionAuthentication, BasicAuthentication]
    filter_backends = [DjangoFilterBackend]
    filterset_class = AthletesFilters
    permission_classes = [IsAuthenticated]

    serializer_classes = {
        "create": serializers.CreateAthleteSerializer,
        "update": serializers.UpdateAthleteSerializer
    }

    def get_queryset(self):
        user = self.request.user
        if user.role == "main_admin" or user.role == "superuser":
            # National-level user can see all athletes
            return self.queryset.all()

        if user.role == "free_dojo" or user.role == "subed_dojo":
            # Dojo-level user sees only their own dojo athletes
            return self.queryset.filter(dojo=user)
        
        raise PermissionDenied("You do not have access to this data.")

    def get_serializer_class(self):
        if self.action == "retrieve":
            user = self.request.user
            if user.role in ["free_dojo", "subed_dojo"]:
                return serializers.NotAdminLikeTypeAthletesSerializer
            return serializers.AthletesSerializer

        return super().get_serializer_class()
    
    def perform_create(self, serializer):
        skip_number = serializer.validated_data.get("skip_number")

        if skip_number == 0:
            # Auto-generate skip_number if it wasn't provided
            last_athlete = Athlete.objects.all().order_by("skip_number").last()
            skip_number = (last_athlete.skip_number if last_athlete else 0) + 1

        serializer.save(skip_number=skip_number)

    @action(detail=False, methods=["get"], url_path="last_five")
    def last_five(self, request):
        # TODO: add authentication
        last_five = Athlete.objects.filter(dojo=request.user).order_by('creation_date')[:5]
        serializer = serializers.AthletesSerializer(last_five, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['delete'], url_path="delete_all")
    def delete_all(self, request):
        deleted_count, _ = Athlete.objects.filter(dojo=request.user).delete()
        if deleted_count <= 1:
            return Response(
                {"message": "Atleta eliminado"},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"message": f"Eliminados {deleted_count} Atletas"},
                status=status.HTTP_200_OK
            )
    
    @action(detail=True, methods=['get'], url_path='unregistered_modalities/(?P<event_id>[^/.]+)')
    def unregistered_modalities(self, request, pk=None, event_id=None):
        try:
            athlete = self.get_object()
            event = Event.objects.get(pk=event_id)
        except Event.DoesNotExist:
            return Response({"detail": "Event not found."}, status=status.HTTP_404_NOT_FOUND)

        # All modalities of the event
        event_disciplines = event.disciplines.all()

        # Modalities where the athlete is already registered
        registered = athlete.disciplines_indiv.filter(event=event)

        # Difference = unregistered
        unregistered = event_disciplines.exclude(id__in=registered.values_list('id', flat=True))

        serializer = dojo_serializers.DisciplinesCompactSerializer(unregistered, many=True)
        return Response(serializer.data)


class TeamsViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    queryset=Team.objects.all()
    serializer_class = serializers.TeamsSerializer
    # authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    serializer_classes = {
        # "create": serializers.CreateAthleteSerializer,
        "update": serializers.UpdateTeamsSerializer
    }

    def get_queryset(self):
        return self.queryset.filter(dojo=self.request.user)

    @action(detail=False, methods=["get"], url_path="last_five")
    def last_five(self, request):
        # TODO: add authentication
        last_five = Team.objects.filter(dojo=request.user).order_by('creation_date')[:5]
        serializer = serializers.TeamsSerializer(last_five, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['delete'], url_path="delete_all")
    def delete_all(self, request):
        deleted_count, _ = Team.objects.filter(dojo=request.user).delete()
        if deleted_count <= 1:
            return Response(
                {"message": "Equipa eliminada"},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"message": f"Eliminadas {deleted_count} Equipas"},
                status=status.HTTP_200_OK
            )


class ClassificationsViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    queryset=Classification.objects.all()
    serializer_class = serializers.AllClassificationsSerializer
    # authentication_classes = [SessionAuthentication, BasicAuthentication]
    # permission_classes = [IsAuthenticated]

    serializer_classes = {
        "create": serializers.CreateClassificationsSerializer,
    }

    @action(detail=False, methods=["get"], url_path="per_comp")
    def per_comp(self, request):
        queryset = Classification.objects.all()
        serialized_data = serializers.AllClassificationsSerializer(queryset, many=True)
        final_classification = {}
        competition = ""
        for classification in serialized_data.data:
            comp_dict = {}
            if competition == "" and classification["competition"] == competition:
                comp_dict[classification['full_category']] = {"first_place": classification["first_place"], 
                                                           "second_place": classification["second_place"],
                                                           "third_place": classification["third_place"]}
            else:
                competition = classification["competition"]
                comp_dict[classification['full_category']] = {"first_place": classification["first_place"], 
                                                           "second_place": classification["second_place"],
                                                           "third_place": classification["third_place"]}
            if competition not in final_classification.keys():
                final_classification[competition] = [comp_dict]
            else:
                final_classification[competition].append(comp_dict)

        return Response([final_classification])
    
    @action(detail=False, methods=["get"], url_path="last_comp_quali")
    def last_comp_quali(self, request):
        last_competition = Event.objects.filter(has_ended=True).order_by('event_date').last()
        if last_competition is None:
            return Response([])
        last_comp_quali = Classification.objects.filter(competition=last_competition.id)
        serialized_data = serializers.ClassificationsSerializer(last_comp_quali, many=True)
        return Response(serialized_data.data)