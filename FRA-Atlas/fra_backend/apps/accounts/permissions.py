"""DRF permission classes enforcing role permission + geographic scope."""
from rest_framework.permissions import BasePermission


class HasFRAPermission(BasePermission):
    """Checks the view's `required_permission` against the user's role, and
    object geography against the user's assigned jurisdiction.

    Views opt in by setting `required_permission = '<CODE>'`.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        required = getattr(view, "required_permission", None)
        if required and not user.has_fra_permission(required):
            return False
        return True

    def has_object_permission(self, request, view, obj):
        user = request.user
        state = getattr(obj, "state", None)
        district_code = getattr(obj, "district_code", None)
        if district_code is None and state is None:
            return True  # non-geographic object
        return user.in_scope(state=state, district_code=district_code)
