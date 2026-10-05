from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


class Command(BaseCommand):
    """Create Daily Tea user groups and permissions."""

    help = "Create and configure Daily Tea user roles."

    def handle(self, *args, **options):
        permissions = {
            "reader": [
                "view_article",
                "view_newsletter",
            ],
            "journalist": [
                "view_article",
                "add_article",
                "change_article",
                "delete_article",
                "view_newsletter",
                "add_newsletter",
                "change_newsletter",
                "delete_newsletter",
            ],
            "editor": [
                "view_article",
                "change_article",
                "delete_article",
                "approve_article",
                "view_newsletter",
                "add_newsletter",
                "change_newsletter",
                "delete_newsletter",
            ],
        }

        for role, permission_codenames in permissions.items():
            group, created = Group.objects.get_or_create(
                name=role.capitalize()
            )

            group.permissions.clear()

            for codename in permission_codenames:
                permission = Permission.objects.get(
                    codename=codename,
                    content_type__app_label="news",
                )

                group.permissions.add(permission)

            action = "created" if created else "updated"

            self.stdout.write(
                self.style.SUCCESS(
                    f"{group.name} group {action}."
                )
            )
