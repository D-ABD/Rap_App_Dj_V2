from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.db.models import Q  # ✅ pour construire des Q dynamiques

def is_staff_like(u) -> bool:
    return bool(getattr(u, "is_staff", False) or getattr(u, "is_admin", False) or getattr(u, "is_superuser", False))

class CanAccessProspectionComment(BasePermission):
    message = "Accès refusé."

    def has_object_permission(self, request, view, obj):
        u = request.user
        if not u or not u.is_authenticated:
            self.message = "Authentification requise."
            return False

        if is_staff_like(u):
            return True

        if hasattr(u, "is_candidat_or_stagiaire") and u.is_candidat_or_stagiaire():
            # Lecture: uniquement non-internes ET appartenant au candidat
            if request.method in SAFE_METHODS:
                return (not obj.is_internal) and (obj.prospection.owner_id == u.id)
            # Écriture/Suppression: idem + doit être l'auteur du commentaire
            return (not obj.is_internal) and (obj.prospection.owner_id == u.id) and (obj.created_by_id == u.id)

        return False


class IsSuperAdminOnly(BasePermission):
    message = "Accès réservé aux superadmins uniquement."
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_superadmin()


class IsAdmin(BasePermission):
    message = "Accès réservé au staff, admin ou superadmin."
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff_or_admin()


class ReadWriteAdminReadStaff(BasePermission):
    message = "Lecture réservée au staff. Écriture réservée aux admins."
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            self.message = "Authentification requise."
            return False
        if request.method in SAFE_METHODS:
            return user.is_staff_or_admin() or user.is_staff
        return user.has_role("admin", "superadmin") or user.is_superuser


class IsStaffOrAbove(BasePermission):
    message = "Accès réservé au staff, admin ou superadmin."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # Vérifie explicitement le rôle
        role = getattr(user, "role", "").lower()
        return (
            getattr(user, "is_staff", False)
            or getattr(user, "is_superuser", False)
            or role in ["staff", "admin", "superadmin"]
        )
class ReadOnlyOrAdmin(BasePermission):
    message = "Lecture publique. Modifications réservées aux admins ou superadmins."
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.has_role("admin", "superadmin")


class IsOwnerOrSuperAdmin(BasePermission):
    message = "Accès refusé : vous n'êtes pas le créateur ni superadmin."
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            self.message = "Authentification requise."
            return False
        return user.is_superadmin() or getattr(obj, 'created_by_id', None) == user.id


class IsOwnerOrStaffOrAbove(BasePermission):
    """
    Autorise staff/admin/superuser.
    Pour les autres, autorise si créateur.
    ✅ Et pour les objets Partenaire, autorise aussi la LECTURE si l'utilisateur
       est owner d'au moins UNE prospection liée à ce partenaire.
    """
    message = "Accès restreint."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_staff_or_admin() or user.is_superuser:
            return True

        # Créateur → OK (R/W selon la vue)
        if getattr(obj, 'created_by_id', None) == user.id:
            return True

        # ✅ Cas particulier Partenaire: lecture autorisée si "attribué via prospection"
        if request.method in SAFE_METHODS and hasattr(obj, "prospections"):
            try:
                if obj.prospections.filter(owner=user).exists():
                    return True
            except Exception:
                pass

        return False


class RestrictToUserOwnedQuerysetMixin:
    """
    Mixin générique: restreint le queryset aux objets 'créés par' l'utilisateur
    pour les non-staff. Permet aux vues de SURCHARGER la visibilité avec
    `user_visibility_q(self, user)`.

    - Par défaut: Q(created_by=user)
    - Une vue peut étendre: ex. Q(created_by=user) | Q(prospections__owner=user)
    """
    user_field = 'created_by'

    def user_visibility_q(self, user):
        # Par défaut: uniquement créés par l'utilisateur
        return Q(**{self.user_field: user})

    def apply_user_scope(self, qs):
        user = self.request.user
        if user.is_authenticated and not (user.is_staff_or_admin() or getattr(user, "is_superuser", False)):
            return qs.filter(self.user_visibility_q(user)).distinct()
        return qs

    def get_queryset(self):
        qs = super().get_queryset()
        return self.apply_user_scope(qs)

