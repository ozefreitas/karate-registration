from django.shortcuts import render
from .models import Bracket, Match
import draw.serializers as serializers
from core.views import MultipleSerializersMixIn
from core.permissions import IsAuthenticatedOrReadOnly
from rest_framework import viewsets, filters, status

# Create your views here.

class BracketViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    queryset=Bracket.objects.all()
    serializer_class=serializers.BracketSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    serializer_classes = {
        "create": serializers.CreateBracketSerializer,
    }


class MatchViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    queryset=Match.objects.all()
    serializer_class=serializers.MatchSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    serializer_classes = {
        "create": serializers.CreateMatchSerializer,
    }