from django.contrib import admin

from apps.misc.models import Policy


# Register your models here.


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    fieldsets = [
        (
            'Policy Information', {
                'fields': [
                    'title',
                    'language',
                    'content',
                ],
            }
        ),
    ]
    list_display = (
        'title',
        'language',
    )
    list_per_page = 20
    search_fields = (
        'title',
        'language',
    )
