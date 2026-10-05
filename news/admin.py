from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Article, Newsletter, Publisher, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Admin configuration for the Daily Tea custom user."""

    fieldsets = UserAdmin.fieldsets + (
        (
            "Daily Tea Profile",
            {
                "fields": (
                    "role",
                    "publisher",
                    "subscribed_publishers",
                    "subscribed_journalists",
                ),
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Daily Tea Profile",
            {
                "fields": (
                    "role",
                    "publisher",
                    "subscribed_publishers",
                    "subscribed_journalists",
                ),
            },
        ),
    )

    def save_related(self, request, form, formsets, change):
        """Clear reader subscriptions for non-reader users."""

        super().save_related(
            request,
            form,
            formsets,
            change,
        )

        user = form.instance
        user.clear_invalid_subscriptions()


admin.site.register(Publisher)
admin.site.register(Article)
admin.site.register(Newsletter)
