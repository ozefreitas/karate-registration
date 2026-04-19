from .roles import Roles
from .permissions import Permissions

ROLE_PERMISSIONS = {
    Roles.MAINADMIN: [
        Permissions.CREATE_EVENT,
        Permissions.DELETE_POST,
        Permissions.VIEW_PREMIUM,
    ],
    Roles.EDITOR: [
        Permissions.CREATE_POST,
    ],
    Roles.USER: [],
}