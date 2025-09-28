from django_filters import rest_framework as filters
from .models import Discipline


class DisciplinesFilters(filters.FilterSet):
    """Filter Disciplines based on event"""
    event_disciplines = filters.CharFilter(field_name='event_disciplines',
                                              method='filter_event_disciplines')

    def filter_event_disciplines(self, queryset, name, value):
        return queryset.filter(event=value)

    class Meta:
        model = Discipline
        fields = []