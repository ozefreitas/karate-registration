from django_filters import rest_framework as filters
from .models import Discipline, Event


class EventsFilters(filters.FilterSet):
    """Filter Events based on different fields"""
    season = filters.CharFilter(field_name='season',
                                              method='filter_season')
    has_ended = filters.BooleanFilter(field_name='has_ended',
                                              method='filter_has_ended')
    has_teams = filters.BooleanFilter(field_name='has_teams',
                                              method='filter_has_teams')
    has_categories = filters.BooleanFilter(field_name='has_categories',
                                              method='filter_has_categories')
    has_registrations = filters.BooleanFilter(field_name='has_registrations',
                                              method='filter_has_registrations')

    def filter_season(self, queryset, name, value):
        return queryset.filter(season=value)
    
    def filter_has_ended(self, queryset, name, value):
        return queryset.filter(has_ended=value)
    
    def filter_has_teams(self, queryset, name, value):
        if not value:
            return queryset.all()
        else:
            return queryset.filter(has_teams=value)
                
    def filter_has_categories(self, queryset, name, value):
        if not value:
            return queryset.all()
        else:
            return queryset.filter(has_categories=value)
        
    def filter_has_registrations(self, queryset, name, value):
        if not value:
            return queryset.all()
        else:
            return queryset.filter(has_registrations=value)


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