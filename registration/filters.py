from django_filters import rest_framework as filters
from registration.models import MonthlyPersonPayment, Person, Classification
from events.models import Event, Discipline
from django.db.models import Q, Count


class PersonsFilters(filters.FilterSet):
    """Filter Persons"""
    not_in_event = filters.CharFilter(method='filter_persons_not_in_event')
    in_category = filters.CharFilter(method='filter_persons_in_category')
    in_gender = filters.CharFilter(method='filter_persons_in_gender')
    is_quotes_legible = filters.BooleanFilter(method='filter_persons_is_quotes_legible')
    is_validated = filters.BooleanFilter(method='filter_persons_is_validated')
    coach_not_in_event = filters.CharFilter(method='filter_coach_not_in_event')
    monthly_payment_status = filters.CharFilter(method="filter_payment")
    in_member_type = filters.CharFilter(method='filter_persons_in_member_type')
    in_user = filters.CharFilter(method='filter_persons_in_user')
    discipline_id = filters.CharFilter(method='filter_discipline_id')

    def filter_persons_not_in_event(self, queryset, name, value):
        event = Event.objects.filter(id=value).first()
        discipline_id = self.data.get("discipline_id")

        discipline = Discipline.objects.filter(id=discipline_id).first()

        if not discipline:
            return queryset.none()

        number_disciplines = event.disciplines.filter(
            is_coach=False,
            is_team=discipline.is_team,
        ).count()

        qs = (
            queryset
            .annotate(
                discipline_count=Count(
                    "disciplines_indiv",
                    filter=Q(
                        disciplines_indiv__event=event,
                        disciplines_indiv__is_coach=False,
                        disciplines_indiv__is_team=discipline.is_team,
                    ),
                    distinct=True,
                )
            )
            .filter(
                member_types__member_type="athlete",
                discipline_count__lt=number_disciplines,
            )
        )

        if discipline.is_team:
            qs = qs.exclude(
                Q(first_element__disciplines_team=discipline) |
                Q(second_element__disciplines_team=discipline) |
                Q(third_element__disciplines_team=discipline)
            )
        
        return qs.distinct()
    
    def filter_persons_in_category(self, queryset, name, value):
        return queryset.filter(category=value)
    
    def filter_persons_in_gender(self, queryset, name, value):
        return queryset.filter(gender=value)
    
    def filter_persons_is_quotes_legible(self, queryset, name, value):
        return queryset.filter(quotes_legible=value)
    
    def filter_persons_is_validated(self, queryset, name, value):
        return queryset.filter(is_validated=value)
    
    def filter_coach_not_in_event(self, queryset, name, value):
        discipline_id = self.data.get("discipline_id")

        return queryset.filter(
            member_types__member_type="coach",
            graduation__lt="8",
        ).exclude(
            disciplines_indiv__id=discipline_id
        )

    def filter_payment(self, queryset, name, value):
        matching_ids = [
            obj.id for obj in queryset
            if obj.current_month_payment() == value
        ]
        return queryset.filter(id__in=matching_ids)
    
    def filter_persons_in_member_type(self, queryset, name, value):
        types = [v.strip() for v in value.split(",") if v.strip()]
        return queryset.filter(member_types__member_type__in=types)

    def filter_persons_in_user(self, queryset, name, value):
        users = [v.strip() for v in value.split(",") if v.strip()]
        return queryset.filter(club__in=users)
    
    def filter_discipline_id(self, queryset, name, value):
        return queryset

    class Meta:
        model = Person
        fields = []


class MonthlyPersonPaymentFilters(filters.FilterSet):
    """Filter Monthly Subscription objects"""

    person = filters.CharFilter(method='filter_person')
    
    def filter_person(self, queryset, name, value):
        """Will retrieve the first occurance with the unique together fields from the member, and retrieve its payments info for all member types"""
        person_to_search = Person.objects.get(id=value)
        return queryset.filter(person=person_to_search)

    class Meta:
        model = MonthlyPersonPayment
        fields = []


class ClassificationsFilters(filters.FilterSet):
    """Filter Monthly Subscription objects"""

    bracket = filters.CharFilter(method='filter_bracket')
    event = filters.CharFilter(method='filter_event')
    
    def filter_bracket(self, queryset, name, value):
        return queryset.filter(bracket = value)
    
    def filter_event(self, queryset, name, value):
        return queryset.filter(bracket__event = value)

    class Meta:
        model = Classification
        fields = []