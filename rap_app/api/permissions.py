from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsSuperAdminOnly(BasePermission):
    """
    Autorise uniquement les superadmins à accéder à cette vue.
    """
    message = "Accès réservé aux superadmins uniquement."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == 'superadmin'
        )


class IsAdmin(BasePermission):
    """
    Autorise uniquement les administrateurs (staff, admin, superadmin) à accéder à cette vue.
    """
    message = "Accès réservé aux membres du staff, admins ou superadmins."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in ['staff', 'admin', 'superadmin']
        )


class ReadWriteAdminReadStaff(BasePermission):
    """
    Lecture : autorisée pour staff, admin, superadmin.
    Écriture : réservée à admin et superadmin uniquement.
    """
    message = "Lecture autorisée pour le staff. Modifications réservées aux admins ou superadmins."

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            self.message = "Authentification requise."
            return False

        role = getattr(user, 'role', None)

        if request.method in SAFE_METHODS:
            if role in ['staff', 'admin', 'superadmin']:
                return True
            self.message = "Lecture réservée au staff, admins ou superadmins."
            return False

        if role in ['admin', 'superadmin']:
            return True

        self.message = "Seuls les admins ou superadmins peuvent modifier cette ressource."
        return False


class IsStaffOrAbove(BasePermission):
    """
    Autorise uniquement le staff, les admins ou les superadmins à accéder à la vue.
    """
    message = "Accès réservé au staff, aux admins ou aux superadmins."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in ['staff', 'admin', 'superadmin']
        )


class ReadOnlyOrAdmin(BasePermission):
    """
    Tout le monde peut lire (GET, HEAD, OPTIONS), seuls les admins ou superadmins peuvent modifier.
    """
    message = "Lecture publique. Modifications réservées aux admins ou superadmins."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return (
            request.user.is_authenticated and
            request.user.role in ['admin', 'superadmin']
        )


class IsOwnerOrSuperAdmin(BasePermission):
    """
    Autorise l'accès si l'utilisateur est le propriétaire OU superadmin.
    """
    message = "Vous ne pouvez accéder qu'à vos propres données, sauf si vous êtes superadmin."

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            self.message = "Authentification requise."
            return False

        if getattr(user, 'role', '') == 'superadmin':
            return True

        return getattr(obj, 'user', None) == user or getattr(obj, 'owner', None) == user


class IsOwnerOrStaffOrAbove(BasePermission):
    """
    Autorise l'accès si l'utilisateur est le propriétaire OU staff/admin/superadmin.
    """
    message = "Accès réservé au propriétaire ou aux membres du staff, admin ou superadmin."

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            self.message = "Authentification requise."
            return False

        if getattr(user, 'role', '') in ['staff', 'admin', 'superadmin']:
            return True

        return getattr(obj, 'user', None) == user or getattr(obj, 'owner', None) == user
 