from django_filters import rest_framework as filters
from .models import Notification


class NotificationsFilters(filters.FilterSet):
    """Filter Notifications"""
    club_notification = filters.CharFilter(field_name='club_notification',
                                              method='filter_club_notification')

    def filter_club_notification(self, queryset, name, value):
        if value == "0":
            return queryset.none()
        return queryset.filter(club_user=value)

    class Meta:
        model = Notification
        fields = []
