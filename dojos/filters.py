from django_filters import rest_framework as filters
from dojos.models import Notification, Discipline

class NotificationsFilters(filters.FilterSet):
    """Filter Notifications"""
    dojo_notification = filters.CharFilter(field_name='dojo_notification',
                                              method='filter_dojo_notification')

    def filter_dojo_notification(self, queryset, name, value):
        if value == "0":
            return queryset.none()
        return queryset.filter(dojo=value)

    class Meta:
        model = Notification
        fields = []


class DisciplinesFilters(filters.FilterSet):
    """Filter Notifications"""
    event_disciplines = filters.CharFilter(field_name='event_disciplines',
                                              method='filter_event_disciplines')

    def filter_event_disciplines(self, queryset, name, value):
        return queryset.filter(event=value)

    class Meta:
        model = Discipline
        fields = []