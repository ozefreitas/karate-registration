from django_filters import rest_framework as filters
from .models import Notification, Category


class NotificationsFilters(filters.FilterSet):
    """Filter Notifications"""
    user_id = filters.CharFilter(field_name='user_id',
                                            method='filter_user_id')
    type = filters.CharFilter(field_name='type', method='filter_notifications_in_type')
    can_remove = filters.BooleanFilter(field_name='can_remove',
                                            method='filter_can_remove')

    def filter_user_id(self, queryset, name, value):
        request = self.request
        user = request.user

        if user.role in ["main_admin", "single_admin", "superuser"]:
            return queryset.filter(club_user=value)

        # if not admin ignore filter and return only their own
        return queryset.filter(club_user=user)
    
    def filter_notifications_in_type(self, queryset, name, value):
        types = [v.strip() for v in value.split(",") if v.strip()]
        return queryset.filter(type__in=types)
    
    def filter_can_remove(self, queryset, name, value):
        if value:
            return queryset.filter(can_remove=True)
        else: return queryset

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
    not_in_discipline = filters.CharFilter(field_name='not_in_discipline',
                                            method='filter_not_in_discipline')
    has_max_athletes = filters.BooleanFilter(field_name='has_max_athletes',
                                            method='filter_has_max_athletes')

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
    
    def filter_not_in_discipline(self, queryset, name, value):
        return queryset.exclude(event_categories__id=value)

    def filter_has_max_athletes(self, queryset, name, value):
        if value == None:
            return queryset
        else:
            return queryset.filter(max_athletes__isnull=not value)
    
    class Meta:
        model = Category
        fields = []