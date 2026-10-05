from rest_framework.permissions import BasePermission


class IsJournalist(BasePermission):
    """Allow access only to journalist users."""

    message = "Only journalists can create articles."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == "journalist"
        )
