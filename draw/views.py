from django.shortcuts import render

from .models import Bracket, Match
import draw.serializers as serializers
from core.views import MultipleSerializersMixIn
from core.permissions import IsAuthenticatedOrReadOnly, IsNationalForPostDelete
from .filters import BracketsFilters, MatchesFilters

from rest_framework import viewsets
from rest_framework.decorators import api_view, action
from rest_framework.response import Response

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


class MatchViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    queryset = Match.objects.select_related(
        'bracket__event',
        'contender_1',
        'contender_2',
        'winner',
        'kataresult',
        'kumiteresult',
    )
    serializer_class=serializers.MatchSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_class = MatchesFilters
    pagination_class = None

    serializer_classes = {
        "create": serializers.CreateMatchSerializer,
    }

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
            "winner": match.winner.id if match.winner else None
        })