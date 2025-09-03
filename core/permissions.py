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
    - Only main_admin/superuser can POST.
    - DELETE: allowed for admins, or for the owner of the notification (obj.dojo).
    - Safe methods are allowed for everyone.
    """
    def has_permission(self, request, view):
        if request.method in ["POST", "PUT", "PATCH"]:
            return (
                request.user.is_authenticated
                and getattr(request.user, "role", None) in ["main_admin", "superuser"]
            )
        return True  # allow other methods to go to object-level check if needed

    def has_object_permission(self, request, view, obj):
        if request.method == "DELETE":
            return (
                getattr(request.user, "role", None) in ["main_admin", "superuser"]
                or obj.dojo == request.user  # owner check
            )
        return True


class IsUnauthenticatedForPost(BasePermission):
    """Allows access to POST for anyone. DELETE and GET are retricted to admin roles"""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS or request.method in ["DELETE"]:
            return bool(request.user and request.user.is_authenticated and (request.user.role == 'main_admin' or request.user.role == 'superuser'))
        return True
    

class IsPayingUserorAdminForGet(BasePermission):
    """Allows access to GET just for subscribing acounts and admin like users"""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated and (request.user.role == 'main_admin' 
                                                                            or request.user.role == 'superuser' 
                                                                            or request.user.role == 'subed_dojo'))
        return True