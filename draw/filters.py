from django_filters import rest_framework as filters
from .models import Bracket


class BracketsFilters(filters.FilterSet):
    """Filter Brackets based on different fields"""
    event = filters.CharFilter(field_name='event',
                                            method='filter_event')

    def filter_event(self, queryset, name, value):
        return queryset.filter(event=value)

    class Meta:
        model = Bracket
        fields = []