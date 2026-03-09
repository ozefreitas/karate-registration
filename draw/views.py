from django.db.models import Q, Count

from .models import Bracket, Match
import draw.serializers as serializers
from core.views import MultipleSerializersMixIn
from core.permissions import IsAuthenticatedOrReadOnly, IsNationalForPostDelete, IsTechnicianOrAdmin
from registration.serializers import CompactPersonSerializer
from registration.models import Person
from .filters import BracketsFilters, MatchesFilters

from rest_framework import viewsets
from rest_framework.decorators import api_view, action
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

# Create your views here.

class BracketViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    queryset=Bracket.objects.all()
    serializer_class=serializers.BracketSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_class = BracketsFilters
    pagination_class = None

    serializer_classes = {
        "create": serializers.CreateBracketSerializer,
    }

    @extend_schema(responses=CompactPersonSerializer(many=True))
    @action(detail=True, methods=["get"], url_path="persons")
    def persons(self, request, pk=None):
        bracket = self.get_object()
        
        persons = Person.objects.filter(
            Q(matches_as_1__bracket=bracket) | Q(matches_as_2__bracket=bracket)
        ).distinct()

        serializer = CompactPersonSerializer(persons, many=True)
        return Response(serializer.data)


class MatchViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    queryset = Match.objects.select_related(
        'bracket__event',
        'contender_1',
        'contender_2',
        'winner',
        'kataresult',
        'kumiteresult',
    ).order_by("created_at")
    serializer_class=serializers.MatchSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_class = MatchesFilters
    pagination_class = None

    serializer_classes = {
        "create": serializers.CreateMatchSerializer,
        "update": serializers.UpdateMatchSerializer,
    }
    

    def perform_update(self, serializer):
        instance = serializer.save()
        if instance.ongoing:
            instance.set_ongoing()

    @action(
        detail=True,
        methods=["patch"],
        url_path="set_winner",
        permission_classes=[IsNationalForPostDelete],
        serializer_class=serializers.PatchMatchWinnerSerializer
    )
    def set_winner(self, request, pk=None):
        match = self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        winner_number = serializer.validated_data["winner"]

        try:
            match.set_winner(winner_number)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)

        return Response({
            "success": True,
            "match_id": match.id,
            "winner": match.winner.id if match.winner else None,
            "is_final": match.round_number == 0,
            "discipline": match.bracket.discipline.name,
            "category": f"{match.bracket.category.name} {match.bracket.category.gender}"
        })

    @action(
        detail=True,
        methods=["patch"],
        url_path="advance_match",
        permission_classes=[IsTechnicianOrAdmin],
        serializer_class=serializers.AdvanceMatchSerializer
    )
    def advance_match(self, request, pk=None):
        current_match = self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        next_match_id = serializer.validated_data["next_match_id"]

        try:
            next_match = Match.objects.get(id=next_match_id, bracket=current_match.bracket)
        except Match.DoesNotExist:
            return Response({"error": "Match not found in this bracket."}, status=404)

        if next_match.contender_1 == None and next_match.contender_2 == None:
            return Response({
            "error": "Partida seguinte não tem pelo menos um dos competidores definidos. Conclua as partidas das rondas anteriores!"
        }, status=404)

        current_match.ongoing = False
        current_match.save(update_fields=["ongoing"])
        next_match.set_ongoing()

        return Response({
            "success": True,
            "next_match_id": next_match.id,
        })

    @action(
        detail=True,
        methods=["patch"],
        url_path="track_back_match",
        permission_classes=[IsTechnicianOrAdmin],
        serializer_class=serializers.PreviousMatchSerializer
    )
    def track_back_match(self, request, pk=None):
        current_match = self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        prev_match_id = serializer.validated_data["prev_match_id"]

        try:
            prev_match = Match.objects.get(id=prev_match_id, bracket=current_match.bracket)
        except Match.DoesNotExist:
            return Response({"error": "Match not found in this bracket."}, status=404)

        if prev_match.contender_1 == None and prev_match.contender_2 == None:
            return Response({
            "error": "Partida anterior não tem pelo menos um dos competidores definidos. Conclua as partidas das rondas anteriores!"
        }, status=404)

        current_match.ongoing = False
        current_match.save(update_fields=["ongoing"])
        prev_match.set_ongoing()

        return Response({
            "success": True,
            "prev_match_id": prev_match.id,
        })