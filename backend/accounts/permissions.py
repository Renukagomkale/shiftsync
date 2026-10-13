from rest_framework.permissions import BasePermission

from .models import User


class IsManager(BasePermission):
    message = "Only managers can do this."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == User.Role.MANAGER)
