from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group as DjangoGroup

from apps.core.models import *


class Group(DjangoGroup):
    class Meta:
        verbose_name = "group"
        verbose_name_plural = "groups"
        proxy = True


class GroupAdmin(BaseGroupAdmin):
    pass


class UserAdmin(BaseUserAdmin):
    list_display = (
        "full_name",
        "email",
        "phone_number",
        "email_verified",
        "is_staff",
        "is_active",
        "is_agent",

    )
    list_editable = (
        "email_verified",
    )
    list_filter = (
        "email",
        "is_staff",
        "is_active",
    )
    list_per_page = 20
    fieldsets = (
        (
            "Login Credentials",
            {
                "fields": (
                    "full_name",
                    "email",
                    "phone_number",
                    "password",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "google_provider",
                    "is_active",
                    "is_staff",
                    "is_agent",
                    "email_verified",
                    "groups",
                    "user_permissions"
                )
            },
        ),
        (
            "Important Dates",
            {
                "fields": (
                    "created",
                    "updated",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            "Personal Information",
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )
    readonly_fields = ("created", "updated",)
    search_fields = ("email",)
    ordering = ("email",)


@admin.register(NormalProfile)
class NormalProfileAdmin(admin.ModelAdmin):
    fieldsets = [
        (
            'Profile Information', {
                'fields': [
                    'user',
                    'image',
                    'date_of_birth',
                ],
            }
        ),
    ]
    list_display = (
        'full_name',
        'phone_number',
        'date_of_birth',
    )
    list_per_page = 20
    search_fields = (
        'phone_number',
    )

    @admin.display(description='Full name')
    def full_name(self, obj):
        return obj.user.full_name

    @admin.display(description='Phone_number')
    def phone_number(self, obj):
        return obj.user.phone_number


@admin.register(AgentProfile)
class AgentProfileAdmin(admin.ModelAdmin):
    fieldsets = [
        (
            'Profile Information', {
                'fields': [
                    'user',
                    'company_name',
                    'license_number',
                    'image',
                    'background_image',
                    'location',
                    'website',
                ],
            }
        ),
    ]
    list_display = (
        'full_name',
        'company_name',
        'phone_number',
        'location',
        'website',
    )
    list_per_page = 20
    search_fields = (
        'company_name',
        'location',
        'website',
    )

    @admin.display(description='Full name')
    def full_name(self, obj):
        return obj.user.full_name

    @admin.display(description='Phone_number')
    def phone_number(self, obj):
        return obj.user.phone_number


admin.site.register(User, UserAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.unregister(DjangoGroup)
