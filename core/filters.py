from django_filters import rest_framework as filters
from .models import Notification, Category


class NotificationsFilters(filters.FilterSet):
    """Filter Notifications"""
    user_id = filters.CharFilter(field_name='user_id',
                                              method='filter_user_id')

    def filter_user_id(self, queryset, name, value):
        return queryset.filter(club_user=value)

    class Meta:
        model = Notification
        fields = []


class CategoriesFilters(filters.FilterSet):
    """Filter Categories"""
    has_min_age = filters.BooleanFilter(field_name='has_min_age',
                                              method='filter_has_min_age')
    has_max_age = filters.BooleanFilter(field_name='has_max_age',
                                              method='filter_has_max_age')
    has_min_grad = filters.BooleanFilter(field_name='has_min_grad',
                                              method='filter_has_min_grad')
    has_max_grad = filters.BooleanFilter(field_name='has_max_grad',
                                              method='filter_has_max_grad')
    has_min_weight = filters.BooleanFilter(field_name='has_min_weight',
                                              method='filter_has_min_weight')
    has_max_weight = filters.BooleanFilter(field_name='has_max_weight',
                                              method='filter_has_max_weight')
    gender = filters.CharFilter(field_name='gender',
                                              method='filter_gender')

    def filter_has_min_age(self, queryset, name, value):
        return queryset.filter(min_age__isnull=not value)

    def filter_has_max_age(self, queryset, name, value):
        return queryset.filter(max_age__isnull=not value)
    
    def filter_has_min_grad(self, queryset, name, value):
        return queryset.filter(min_grad__isnull=not value)
    
    def filter_has_max_grad(self, queryset, name, value):
        return queryset.filter(max_grad__isnull=not value)

    def filter_has_min_weight(self, queryset, name, value):
        return queryset.filter(min_weight__isnull=not value)
    
    def filter_has_max_weight(self, queryset, name, value):
        return queryset.filter(max_weight__isnull=not value)
    
    def filter_gender(self, queryset, name, value):
        return queryset.filter(gender=value)
    
    class Meta:
        model = Category
        fields = []