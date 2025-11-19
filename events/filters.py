from django_filters import rest_framework as filters
from .models import Discipline, Event


class EventsFilters(filters.FilterSet):
    """Filter Events based on different fields"""
    season = filters.CharFilter(field_name='season',
                                              method='filter_season')

    def filter_season(self, queryset, name, value):
        return queryset.filter(season=value)

    class Meta:
        model = Event
        fields = []


class DisciplinesFilters(filters.FilterSet):
    """Filter Disciplines based on event"""
    event_disciplines = filters.CharFilter(field_name='event_disciplines',
                                              method='filter_event_disciplines')
    is_coach = filters.BooleanFilter(field_name='is_coach',
                                              method='filter_is_coach')
    is_team = filters.BooleanFilter(field_name='is_team',
                                              method='filter_is_team')

    def filter_event_disciplines(self, queryset, name, value):
        return queryset.filter(event=value)
    
    def filter_is_coach(self, queryset, name, value):
        return queryset.filter(is_coach=value)
    
    def filter_is_team(self, queryset, name, value):
        return queryset.filter(is_team=value)

    class Meta:
        model = Discipline
        fields = []