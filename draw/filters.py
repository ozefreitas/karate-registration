from django_filters import rest_framework as filters
from .models import Bracket, Match, ScoringEntry


class BracketsFilters(filters.FilterSet):
    """Filter Brackets based on different fields"""
    event = filters.CharFilter(field_name='event',
                                            method='filter_event')

    def filter_event(self, queryset, name, value):
        return queryset.filter(event=value)

    class Meta:
        model = Bracket
        fields = []


class MatchesFilters(filters.FilterSet):
    """Filter Matches based on different fields"""
    event = filters.CharFilter(field_name='bracket__event', method='filter_event')
    bracket = filters.CharFilter(field_name='bracket', method="filter_bracket")

    def filter_event(self, queryset, name, value):
        return queryset.filter(bracket__event=value)
    
    def filter_bracket(self, queryset, name, value):
        return queryset.filter(bracket=value)

    class Meta:
        model = Match
        fields = []


class ScoringEntriesFilters(filters.FilterSet):
    """Filter ScoringEntries based on different fields"""
    event = filters.CharFilter(field_name='bracket__event', method='filter_event')
    bracket = filters.CharFilter(field_name='bracket', method="filter_bracket")

    def filter_event(self, queryset, name, value):
        return queryset.filter(scoring_round__bracket__event=value)
    
    def filter_bracket(self, queryset, name, value):
        return queryset.filter(scoring_round__bracket=value)

    class Meta:
        model = ScoringEntry
        fields = []