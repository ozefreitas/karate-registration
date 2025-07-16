from django.shortcuts import render
from rest_framework import viewsets, filters, status
from core.permissions import IsAuthenticatedOrReadOnly, IsNationalForPostDelete
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import Category
from .serializers import CategorySerializer, CreateCategorySerializer

# Create your views here.

class MultipleSerializersMixIn:
    serializer_classes = {}

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, self.serializer_class)
    

class CategoriesViewSet(MultipleSerializersMixIn, viewsets.ModelViewSet):
    queryset=Category.objects.all()
    serializer_class=CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    serializer_classes = {
        "create": CreateCategorySerializer,
    }