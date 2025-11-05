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
    - DELETE: allowed for admins, or for the owner of the notification (obj.club_user).
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
                or obj.club_user == request.user  # owner check
            )
        return True


class IsUnauthenticatedForPost(BasePermission):
    """
    Allows access to POST for anyone.
    Safe methods and DELETE are restricted to admin roles.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS or request.method in ["GET", "DELETE"]:
            return bool(
                request.user
                and request.user.is_authenticated
                and (
                    request.user.role in ['main_admin', 'single_admin', 'superuser']
                )
            )
        elif request.method == "POST":
            return True
        return False
    

class IsPayingUserorAdminForGet(BasePermission):
    """Allows access to GET just for subscribing acounts and admin like users"""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated and (request.user.role == 'main_admin' 
                                                                            or request.user.role == 'superuser' 
                                                                            or request.user.role == 'subed_club'))
    

class IsAdminRoleorHigher(BasePermission):
    """Allows access the current url in which is used if the user has an admin like role or higher"""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (request.user.role == 'main_admin' 
                                                                            or request.user.role == 'superuser' 
                                                                            or request.user.role == 'single_admin'))
    

class IsAdminRoleorHigherForGET(BasePermission):
    """Allows access to a GET request if the user has an admin like role or higher"""
    def has_permission(self, request, view):
        if request.method == "GET":
            return bool(request.user and request.user.is_authenticated and (request.user.role == 'main_admin' 
                                                                            or request.user.role == 'superuser' 
                                                                            or request.user.role == 'single_admin'))


class IsGETforClubs(BasePermission):
    """Allows access to GET request for clubs viewset, everything else is restricted to admin like roles"""
    def has_permission(self, request, view):
        if request.method == "GET":
            return True
        else:
            return bool(request.user and request.user.is_authenticated and (request.user.role == 'main_admin' 
                                                                            or request.user.role == 'superuser' 
                                                                            or request.user.role == 'single_admin'))


class AthletePermission(BasePermission):
    """
    Permission used for Athletes and Teams.
    - Admin-like users (main_admin, single_admin, superuser) have access to everything.
    - Paying users (subed_club) have access to SAFE_METHODS, PUT, PATCH.
    - Free users (free_club) only can GET.
    - All others are denied.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        role = getattr(request.user, "role", None)
        if role in ['main_admin', 'single_admin', 'superuser']:
            return True

        if role == 'subed_club':
            # if request.method in SAFE_METHODS or request.method in ["PUT", "PATCH"]:
            if request.method in SAFE_METHODS or request.method in ["PUT", "PATCH", "POST", "DELETE"]:
                return True
            return False
        
        if role == "free_club":
            return bool(request.method in SAFE_METHODS or request.method == "PATCH")

        return False

    def has_object_permission(self, request, view, obj):
        role = getattr(request.user, "role", None)

        # Admins can access all
        if role in ['main_admin', 'single_admin', 'superuser']:
            return True

        # Clubs only access their own athletes
        if role == 'subed_club':
            return obj.club == request.user

        return False
    


class EventPermission(BasePermission):
    """
    Permission used for Events.
    - Admin-like users (main_admin, single_admin, superuser) have access to everything.
    - Other users have access to SAFE_METHODS, PUT, PATCH.
    - All others are denied.
    """
    def has_permission(self, request, view):
        if request.method == "GET":
            return True

        if not request.user or not request.user.is_authenticated:
            return False

        role = getattr(request.user, "role", None)
        if role in ['main_admin', 'single_admin', 'superuser']:
            return True

        else:
            if request.method in SAFE_METHODS or request.method in ["PUT", "PATCH"]:
                return True
            return False