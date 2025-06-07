from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAuthenticatedOrReadOnly(BasePermission):
    """
    Allows access to safe methods (GET, HEAD, OPTIONS) for anyone,
    but restricts POST, PUT, DELETE, etc. to authenticated users.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated