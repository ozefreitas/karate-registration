from django_filters import rest_framework as filters
from registration.models import Athlete
from events.models import Event
from django.db.models import Q, Count


class AthletesFilters(filters.FilterSet):
    """Filter Atlhetes not in comp_id"""
    not_in_event = filters.CharFilter(method='filter_athletes_not_in_event')
    in_category = filters.CharFilter(method='filter_athletes_in_category')
    in_gender = filters.CharFilter(method='filter_athletes_in_gender')

    def filter_athletes_not_in_event(self, queryset, name, value):
        event = Event.objects.filter(id=value).first()
        number_disciplines = event.disciplines.count()

        # no disciplines just returns the ones still not in that event
        if number_disciplines == 0:
            return queryset.exclude(general_events__id=value)

        else: return queryset
        
        # # if the event is an encounter all students are retrieved
        # if event.encounter:
        #     return queryset.annotate(
        #         discipline_count=Count('disciplines_indiv', filter=Q(disciplines_indiv__event=event), distinct=True)
        #         ).filter(
        #             discipline_count__lt=1
        #             )

        # # if event is not an encounter (competition) only competitior are retrieved
        # return queryset.annotate(
        #     discipline_count=Count('disciplines_indiv', filter=Q(disciplines_indiv__event=event), distinct=True)
        #     ).filter(
        #         competitor=True,
        #         discipline_count__lt=number_disciplines
        #         )

    
    def filter_athletes_in_category(self, queryset, name, value):
        return queryset.filter(category=value)
    
    def filter_athletes_in_gender(self, queryset, name, value):
        return queryset.filter(gender=value)

    class Meta:
        model = Athlete
        fields = []