from django_filters import rest_framework as filters
from registration.models import Member, MonthlyMemberPayment
from events.models import Event
from django.db.models import Q, Count
from registration.utils.utils import get_real_member


class MembersFilters(filters.FilterSet):
    """Filter Atlhetes not in comp_id"""
    not_in_event = filters.CharFilter(method='filter_members_not_in_event')
    in_category = filters.CharFilter(method='filter_members_in_category')
    in_gender = filters.CharFilter(method='filter_members_in_gender')
    is_quotes_legible = filters.BooleanFilter(method='filter_members_is_quotes_legible')
    is_validated = filters.BooleanFilter(method='filter_members_is_validated')
    coach_not_in_event = filters.CharFilter(method='filter_coach_not_in_event')
    monthly_payment_status = filters.CharFilter(method="filter_payment")
    in_member_type = filters.CharFilter(method='filter_members_in_member_type')

    def filter_members_not_in_event(self, queryset, name, value):
        event = Event.objects.filter(id=value).first()
        number_disciplines = event.disciplines.filter(is_coach=False).count()

        # no disciplines just returns the ones still not in that event
        if number_disciplines == 0:
            return queryset.exclude(general_events__id=value)
        
        # if the event is an encounter all students are retrieved
        if event.encounter:
            return queryset.annotate(
                discipline_count=Count('disciplines_indiv', filter=Q(disciplines_indiv__event=event), distinct=True)
                ).filter(
                    discipline_count__lt=1
                    )

        # if event is not an encounter (competition) only competitior are retrieved
        return queryset.annotate(
            discipline_count=Count('disciplines_indiv', filter=Q(disciplines_indiv__event=event), distinct=True)
            ).filter(
                member_type="athlete",
                discipline_count__lt=number_disciplines
                )
    
    def filter_members_in_category(self, queryset, name, value):
        return queryset.filter(category=value)
    
    def filter_members_in_gender(self, queryset, name, value):
        return queryset.filter(gender=value)
    
    def filter_members_is_quotes_legible(self, queryset, name, value):
        return queryset.filter(quotes_legible=value)
    
    def filter_members_is_validated(self, queryset, name, value):
        return queryset.filter(is_validated=value)
    
    def filter_coach_not_in_event(self, queryset, name, value):
        event = Event.objects.filter(id=value).first()
        number_disciplines = event.disciplines.filter(is_coach=True).count()

        return queryset.annotate(
            discipline_count=Count('disciplines_indiv', filter=Q(disciplines_indiv__event=event), distinct=True)
            ).filter(
                member_type="coach",
                discipline_count__lt=number_disciplines
                )

    def filter_payment(self, queryset, name, value):
        matching_ids = [
            obj.id for obj in queryset
            if obj.current_month_payment() == value
        ]
        return queryset.filter(id__in=matching_ids)
    
    def filter_members_in_member_type(self, queryset, name, value):
        types = [v.strip() for v in value.split(",") if v.strip()]
        return queryset.filter(member_type__in=types)

    class Meta:
        model = Member
        fields = []



class MonthlyMemberPaymentFilters(filters.FilterSet):
    """Filter Monthly Subscription objects"""

    member = filters.CharFilter(method='filter_member')
    
    def filter_member(self, queryset, name, value):
        """Will retrieve the first occurance with the unique together fields from the member, and retrieve its payments info for all member types"""
        member_to_search = Member.objects.get(id=value)
        real_member = get_real_member(member_to_search)
        return queryset.filter(member=real_member)

    class Meta:
        model = MonthlyMemberPayment
        fields = []