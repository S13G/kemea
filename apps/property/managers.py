from django.db import models


class PropertyManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('lister', 'property_type', 'property_state',
                                                     'ad_category').prefetch_related('features')


class FavoritePropertyManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('property', 'user')
