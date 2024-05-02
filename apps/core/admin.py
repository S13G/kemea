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
        "username",
        "email",
        "email_verified",
        "is_staff",
        "is_active",

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
                    "username",
                    "email",
                    "password",
                    "avatar",
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


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    fieldsets = [
        (
            'Profile Information', {
                'fields': [
                    'avatar',
                    'date_of_birth',
                    'phone_number',
                    'followers',
                    'tokens'
                ],
            }
        ),
    ]
    list_display = (
        'full_name',
        'phone_number',
        'date_of_birth',
        'followers',
        'tokens'
    )
    list_per_page = 20
    search_fields = (
        'phone_number',
        'followers',
        'tokens'
    )

    @admin.display(description='Full name')
    def full_name(self, obj):
        return obj.user.full_name


admin.site.register(User, UserAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.unregister(DjangoGroup)
