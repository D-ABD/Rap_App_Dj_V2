from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.db.models import Q

from .roles import is_admin_like, is_candidate, is_staff_like, is_staff_or_staffread




class CanAccessProspectionComment(BasePermission):
    message = "Accès refusé."

    def has_object_permission(self, request, view, obj):
        u = request.user
        if not u or not u.is_authenticated:
            self.message = "Authentification requise."
            return False

        role = str(getattr(u, "role", "")).lower()

        # --- Admin / superadmin → full access ---
        if is_admin_like(u):
            return True

        # --- Staff (mais pas staff_read) → full access ---
        if is_staff_like(u) and role != "staff_read":
            return True

        # --- Staff_read → lecture seule ---
        if role == "staff_read":
            return request.method in SAFE_METHODS

        # --- Candidat / stagiaire ---
        if is_candidate(u):
            if request.method in SAFE_METHODS:
                return (not obj.is_internal) and (obj.prospection.owner_id == u.id)
            return (
                (not obj.is_internal)
                and (obj.prospection.owner_id == u.id)
                and (obj.created_by_id == u.id)
            )

        # --- Autres rôles : lecture seule si queryset passe, écriture si auteur ---
        if request.method in SAFE_METHODS:
            return True
        return obj.created_by_id == u.id


class IsSuperAdminOnly(BasePermission):
    message = "Accès réservé aux superadmins uniquement."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_superadmin()


class IsAdmin(BasePermission):
    message = "Accès réservé au staff, admin ou superadmin."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff_or_admin()


class ReadWriteAdminReadStaff(BasePermission):
    """
    Lecture autorisée aux staff et staff_read.
    Écriture autorisée uniquement aux admins/superadmins.
    """
    message = "Lecture réservée au staff/staff_read. Écriture réservée aux admins."

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            self.message = "Authentification requise."
            return False

        role = str(getattr(user, "role", "")).lower()

        # Lecture
        if request.method in SAFE_METHODS:
            return (
                is_staff_or_staffread(user)
                or user.is_staff_or_admin()
                or role == "staff_read"
            )

        # Écriture
        return user.has_role("admin", "superadmin") or user.is_superuser


class IsStaffOrAbove(BasePermission):
    message = "Accès réservé au staff, staff_read, admin ou superadmin."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # Bloque explicitement candidats/stagiaires
        if is_candidate(user):
            return False

        role = str(getattr(user, "role", "")).lower()

        # superuser → accès complet
        if getattr(user, "is_superuser", False):
            return True

        # staff/admin → accès complet
        if is_staff_or_staffread(user) or role in {"staff", "admin", "superadmin"}:
            return True

        # staff_read → accès lecture seule
        if role == "staff_read":
            return request.method in SAFE_METHODS

        return False


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
        return user.is_superadmin() or getattr(obj, "created_by_id", None) == user.id


class IsOwnerOrStaffOrAbove(BasePermission):
    """
    Autorise :
    - staff/admin/superuser (accès complet)
    - staff_read (lecture seule)
    - créateur OU owner de l’objet
    - pour Partenaire : lecture possible si user est owner d’une prospection liée
    """
    message = "Accès restreint."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user

        role = str(getattr(user, "role", "")).lower()

        # --- Admin / Superuser ---
        if is_admin_like(user):
            return True

        # --- Staff complet ---
        if is_staff_like(user) and role != "staff_read":
            return True

        # --- Staff_read : lecture seule ---
        if is_staff_or_staffread(user) and request.method in SAFE_METHODS:
            return True

        # --- Owner direct ---
        if getattr(obj, "owner_id", None) == user.id:
            return True

        # --- Créateur ---
        if getattr(obj, "created_by_id", None) == user.id:
            return True

        # --- Cas particulier Partenaire ---
        if request.method in SAFE_METHODS and hasattr(obj, "prospections"):
            try:
                if obj.prospections.filter(owner_id=user.id).exists():
                    return True
            except Exception:
                pass

        return False


class UserVisibilityScopeMixin:
    """
    Mixin générique: restreint le queryset aux objets 'créés par' l'utilisateur
    pour les non-staff. Permet aux vues de SURCHARGER la visibilité avec
    `user_visibility_q(self, user)`.

    - Par défaut: Q(created_by=user)
    - Une vue peut étendre: ex. Q(created_by=user) | Q(prospections__owner=user)
    """
    user_field = "created_by"

    def user_visibility_q(self, user):
        # Par défaut: uniquement créés par l'utilisateur
        return Q(**{self.user_field: user})

    def apply_user_scope(self, qs):
        user = self.request.user
        if user.is_authenticated and not (
            user.is_staff_or_admin() or getattr(user, "is_superuser", False)
        ):
            return qs.filter(self.user_visibility_q(user)).distinct()
        return qs

    def get_queryset(self):
        qs = super().get_queryset()
        return self.apply_user_scope(qs)
