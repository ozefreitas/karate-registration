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
    

class IsNationalForPostDelete(BasePermission):
    """
    Allows POST and DELETE only for users with role 'main_admin'.
    Other methods are allowed (or denied) based on default behavior.
    """
    def has_permission(self, request, view):
        if request.method in ['POST', 'DELETE']:
            return bool(request.user and request.user.is_authenticated and request.user.role == 'main_admin')
        return True


class IsUnauthenticatedForPost(BasePermission):
    """Allows access to POST for anyone. DELETE and GET are retricted to admin roles"""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS or request.method in ["DELETE"]:
            return bool(request.user and request.user.is_authenticated and (request.user.role == 'main_admin' or request.user.role == 'superuser'))
        return True