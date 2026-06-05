from .models import Bracket, Match, ScoringRound, ScoringEntry
import draw.serializers as serializers
from core.views import MultipleSerializersMixIn
from core.permissions import IsAuthenticatedOrReadOnly, IsTechnicianOrAdmin, IsTechnicianOrAdminforPOST
from registration.serializers.base import CompactPersonSerializer
from registration.serializers.serializers import ClassificationsSerializer
from registration.models import Person, Classification
from .filters import BracketsFilters, MatchesFilters, ScoringEntriesFilters

from rest_framework import viewsets
from rest_framework.decorators import api_view, action
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from django.utils import timezone

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
            disciplinemember__category=bracket.category,
            disciplinemember__discipline=bracket.discipline,
        )

        serializer = CompactPersonSerializer(persons, many=True)
        return Response(serializer.data)
    
    @action(
        detail=True,
        methods=["post"],
        url_path="officialize",
        permission_classes=[IsTechnicianOrAdminforPOST],
    )
    def officialize(self, request, pk=None):
        bracket = self.get_object()

        if bracket.draw_type == "Torneio/Finais":
            matches = Match.objects.filter(bracket=bracket).select_related("winner", "contender_1", "contender_2")

            final = matches.filter(round_number=0, match_number=1).first()
            if not final or not final.winner:
                return Response({"error": "Ainda não existe um vencedor para este Escalão! Termine todas as partidas."}, status=400)

            third_place_match = matches.filter(round_number=0, is_third_place=True).first()
            if not third_place_match or not third_place_match.winner:
                return Response({"error": "Ainda não existe um terceiro classificado para este Escalão!"}, status=400)

            # Derive podium
            first = final.winner
            second = final.contender_1 if final.contender_2 == first else final.contender_2
            third = third_place_match.winner

        elif bracket.draw_type == "Misto":
            scoring_entries = ScoringEntry.objects.filter(scoring_round__bracket=bracket).select_related("person")

            first = scoring_entries.filter(rank=1).first().person
            second = scoring_entries.filter(rank=2).first().person
            third = scoring_entries.filter(rank=3).first().person

        # reset if mistake
        Classification.objects.filter(bracket=bracket).delete()

        Classification.objects.create(bracket=bracket, person=first, place=1)
        Classification.objects.create(bracket=bracket, person=second, place=2)
        Classification.objects.create(bracket=bracket, person=third, place=3)

        serializer = ClassificationsSerializer(
            Classification.objects.filter(bracket=bracket).order_by("place"),
            many=True
        )

        bracket.officialized_at = timezone.now()
        bracket.save(update_fields=["officialized_at"])

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
        "partial_update": serializers.UpdateMatchSerializer
    }

    def perform_update(self, serializer):
        instance = serializer.save()
        if instance.ongoing and instance.is_final and instance.winner != None:
            instance.ongoing = False
            instance.save()
        if instance.ongoing:
            instance.set_ongoing()

    @action(
        detail=True,
        methods=["patch"],
        url_path="set_winner",
        permission_classes=[IsTechnicianOrAdmin],
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
        
        # if final, auto goes to not ongoing
        if match.round_number == 0 and match.match_number == 1:
            match.ongoing = False
            match.save()

        return Response({
            "success": True,
            "match_id": match.id,
            "winner": match.winner.id if match.winner else None,
            "is_final": match.round_number == 0 and match.match_number == 1,
            "is_third_place": match.is_third_place,
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


class ScoringEntryViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    queryset = ScoringEntry.objects.select_related(
        'scoring_round__bracket__event',
        'scoring_round__bracket',
        "person",
        "scoring_result",
    ).order_by("created_at")
    serializer_class=serializers.ScoringEntrySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_class = ScoringEntriesFilters
    pagination_class = None

    serializer_classes = {
        "create": serializers.CreateMatchSerializer,
        "update": serializers.UpdateScoringEntrySerializer,
        "partial_update": serializers.UpdateScoringEntrySerializer
    }

    def perform_update(self, serializer):
        instance = serializer.save()
        if instance.ongoing:
            instance.set_ongoing()
