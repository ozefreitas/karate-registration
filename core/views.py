from django.shortcuts import render
from core.permissions import IsAuthenticatedOrReadOnly, IsNationalForPostDelete
from .models import Category
from .serializers import CategorySerializer, CreateCategorySerializer, CompactCategorySerializer

from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser

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
        "retrieve": CompactCategorySerializer
    }

    @action(detail=False, methods=['delete'], url_path="delete_all")
    def delete_all(self, request):
        # CAREFUL as all categories is for now the onlu ones
        deleted_count, _ = Category.objects.all().delete()
        if deleted_count <= 1:
            return Response(
                {"message": "Escalão eliminado"},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"message": f"Eliminados {deleted_count} Escalões"},
                status=status.HTTP_200_OK
            )