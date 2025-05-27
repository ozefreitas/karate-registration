from django_filters import rest_framework as filters
from registration.models import Individual, Athlete


class IndividualFilters(filters.FilterSet):
    """Filter Individuals in comp_id"""
    in_competition = filters.CharFilter(field_name='in_competition',
                                              method='filter_individuals_in_competition')

    def filter_individuals_in_competition(self, queryset, name, value):
        return queryset.filter(competition=value)

    class Meta:
        model = Individual
        fields = []


class AthletesFilters(filters.FilterSet):
    """Filter Atlhetes not in comp_id"""
    not_in_competition = filters.CharFilter(field_name='not_in_competition',
                                              method='filter_athletes_not_in_competition')

    def filter_athletes_not_in_competition(self, queryset, name, value):
        return queryset.exclude(individual__competition_id=value)

    class Meta:
        model = Athlete
        fields = []