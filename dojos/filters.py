from django_filters import rest_framework as filters
from dojos.models import Notification

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