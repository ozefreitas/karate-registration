from django_filters import rest_framework as filters
from registration.models import Individual


class IndividualFilters(filters.FilterSet):
    """Filter Individuals in comp_id"""
    in_competition = filters.CharFilter(field_name='in_competition',
                                              method='filter_individuals_in_competition')

    def filter_individuals_in_competition(self, queryset, name, value):
        print(value)
        return queryset.filter(competition=value)

    class Meta:
        model = Individual
        fields = []