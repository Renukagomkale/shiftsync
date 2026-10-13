from rest_framework.permissions import SAFE_METHODS, BasePermission

from accounts.models import User


class IsBusinessMember(BasePermission):
    message = "Join or create a business first."

    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.business_id)


class ManagerWritesMemberReads(BasePermission):
    message = "Only managers can change the schedule."

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or request.user.role == User.Role.MANAGER
