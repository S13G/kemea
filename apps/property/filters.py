from datetime import timedelta

from django.utils import timezone
from django_filters import FilterSet, filters

from apps.property.models import AdCategory, PropertyType, PropertyFeature, Property


class AdFilter(FilterSet):
    ad_category = filters.ModelChoiceFilter(queryset=AdCategory.objects.all())
    # ad_category__name = filters.CharFilter(lookup_expr='exact')


class PropertyAdFilter(FilterSet):
    property_type = filters.ModelChoiceFilter(queryset=PropertyType.objects.all())
    price_min = filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_max = filters.NumberFilter(field_name='price', lookup_expr='lte')
    surface_build_min = filters.NumberFilter(field_name='surface_build', lookup_expr='gte')
    surface_build_max = filters.NumberFilter(field_name='surface_build', lookup_expr='lte')
    rooms = filters.NumberFilter(field_name='number_of_rooms')
    floors = filters.NumberFilter(field_name='floors')
    features = filters.ModelMultipleChoiceFilter(queryset=PropertyFeature.objects.all())

    # Custom filter for last week
    last_week = filters.CharFilter(method='filter_last_week')

    # Custom filter for last month
    last_month = filters.CharFilter(method='filter_last_month')

    # Custom filter for last 24 hours
    last_24_hours = filters.CharFilter(method='filter_last_24_hours')

    @staticmethod
    def filter_last_week(queryset, name, value):
        if value.lower() == 'true':
            start_date = timezone.now() - timedelta(days=7)
            return queryset.filter(created__gte=start_date)
        return queryset

    @staticmethod
    def filter_last_month(queryset, name, value):
        if value.lower() == 'true':
            start_date = timezone.now() - timedelta(days=30)
            return queryset.filter(created__gte=start_date)
        return queryset

    @staticmethod
    def filter_last_24_hours(queryset, name, value):
        if value.lower() == 'true':
            start_date = timezone.now() - timedelta(hours=24)
            return queryset.filter(created__gte=start_date)
        return queryset

    class Meta:
        model = Property
        fields = ['property_type', 'price_min', 'price_max', 'surface_build_min', 'surface_build_max',
                  'rooms', 'floors', 'features', 'last_week', 'last_month', 'last_24_hours']
