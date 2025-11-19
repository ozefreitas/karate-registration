from django_filters import rest_framework as filters
from .models import Notification


class NotificationsFilters(filters.FilterSet):
    """Filter Notifications"""
    user_id = filters.CharFilter(field_name='user_id',
                                              method='filter_user_id')

    def filter_user_id(self, queryset, name, value):
        return queryset.filter(club_user=value)

    class Meta:
        model = Notification
        fields = []
