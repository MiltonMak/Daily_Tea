from django.conf import settings
from rest_framework.permissions import BasePermission


class InternalAPIKeyPermission(BasePermission):
    """
    Allows authenticated API users or trusted internal requests.
    """

    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            return True

        internal_key = request.headers.get("X-Internal-API-Key")

        return (
            internal_key is not None
            and internal_key == settings.DAILY_TEA_INTERNAL_API_KEY
        )