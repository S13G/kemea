from django.contrib import admin

from apps.property.models import *


# Register your models here.


@admin.register(AdCategory)
class AdCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

    def has_add_permission(self, request):
        return False if self.model.objects.count() == 2 else True


@admin.register(PropertyType)
class PropertyTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    list_per_page = 20
    search_fields = ('name',)


@admin.register(PropertyState)
class PropertyStateAdmin(admin.ModelAdmin):
    list_display = ('name',)
    list_per_page = 20
    search_fields = ('name',)


@admin.register(PropertyFeature)
class PropertyFeatureAdmin(admin.ModelAdmin):
    list_display = ('name',)
    list_per_page = 20
    search_fields = ('name',)


class PropertyMediaInline(admin.TabularInline):
    model = PropertyMedia
    extra = 3
    min_num = 1


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    autocomplete_fields = (
        'property_type',
        'property_state',
        'features'
    )
    inlines = [PropertyMediaInline]
    list_display = (
        'name',
        'property_type',
        'property_state',
        'price',
        'discount',
        'discounted_price',
        'name_of_lister',
        'ad_status',
        'terminated',
    )
    list_filter = ('ad_status',)
    list_per_page = 20
    search_fields = (
        'title',
        'description',
        'property_type__name',
        'property_state__name',
        'name_of_lister',
        'ad_status'
        'price',
    )
