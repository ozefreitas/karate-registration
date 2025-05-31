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
    in_category = filters.CharFilter(field_name='in_category',
                                              method='filter_athletes_in_category')
    in_gender = filters.CharFilter(field_name='in_gender',
                                              method='filter_athletes_in_gender')

    def filter_athletes_not_in_competition(self, queryset, name, value):
        return queryset.exclude(individual__competition_id=value)
    
    def filter_athletes_in_category(self, queryset, name, value):
        return queryset.filter(category=value)
    
    def filter_athletes_in_gender(self, queryset, name, value):
        return queryset.filter(gender=value)

    class Meta:
        model = Athlete
        fields = []