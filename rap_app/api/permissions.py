from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.db.models import Q

from .roles import is_admin_like, is_candidate, is_declic_staff, is_prepa_staff, is_staff_like, is_staff_or_staffread, is_staff_read, is_staff_standard, staff_centre_ids




class CanAccessProspectionComment(BasePermission):
    """
    Accès global à la ressource 'ProspectionComment' :
    - Le filtrage réel par centre ou propriétaire est géré dans le scope
      (UserVisibilityScopeMixin ou get_queryset).
    - Cette permission s'assure simplement que l'utilisateur est authentifié.
    """
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
        if not user or not user.is_authenticated:
            self.message = "Authentification requise."
            return False

        role = str(getattr(user, "role", "")).lower()

        # 🔹 Lecture
        if request.method in SAFE_METHODS:
            return (
                is_staff_or_staffread(user)
                or is_admin_like(user)
                or role == "staff_read"
            )

        # 🔹 Écriture
        return is_admin_like(user) or user.is_superuser

class IsStaffOrAbove(BasePermission):
    message = "Accès réservé au staff, staff_read, admin ou superadmin."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # ❌ Exclure les candidats
        if is_candidate(user):
            return False

        # ✅ Admins → accès complet
        if is_admin_like(user):
            return True

        role = str(getattr(user, "role", "")).lower()

        # ✅ Staff_read → lecture seule
        if role == "staff_read":
            return request.method in SAFE_METHODS

        # ✅ Staff standard uniquement → accès complet
        if role == "staff":
            return True

        # ❌ EXCLUSION des declic_staff et prepa_staff
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
    - staff/admin/superuser → accès complet
    - staff_read → lecture seule
    - créateur ou owner de l’objet
    - pour Partenaire : lecture possible si user est owner d’une prospection liée
    """
    message = "Accès restreint."

    def has_permission(self, request, view):
        user = request.user
        role = str(getattr(user, "role", "")).lower()

        # 🔒 staff_read : lecture seule globale (bloque POST, PUT, PATCH, DELETE)
        if role == "staff_read" and request.method not in SAFE_METHODS:
            return False

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

        # --- Staff_read : lecture seule uniquement ---
        if role == "staff_read":
            return request.method in SAFE_METHODS

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
    pour les rôles non-staff. 

    - Admin/superadmin → accès complet
    - Staff/staff_read → pas de restriction `created_by`
    - Autres → Q(created_by=user)
    """
    user_field = "created_by"

    def user_visibility_q(self, user):
        # Par défaut: uniquement créés par l'utilisateur
        return Q(**{self.user_field: user})

    def apply_user_scope(self, qs):
        user = self.request.user

        if not user.is_authenticated:
            return qs.none()

        # 🔑 Admin/superadmin → full accès
        if is_admin_like(user):
            return qs

        # 👩‍💼 Staff / StaffRead → pas de restriction created_by
        if is_staff_or_staffread(user):
            return qs

        # 🚫 Autres → limité à created_by
        return qs.filter(self.user_visibility_q(user)).distinct()

    def get_queryset(self):
        qs = super().get_queryset()
        return self.apply_user_scope(qs)

class IsStaffReadOnly(BasePermission):
    """
    🔒 Permission spéciale pour les utilisateurs `staff_read` :
    - lecture seule (GET, HEAD, OPTIONS)
    - refus de toute écriture (POST, PUT, PATCH, DELETE)
    """
    message = "Accès en lecture seule uniquement pour le rôle staff_read."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # Si le user est staff_read → lecture seule
        if str(getattr(user, "role", "")).lower() == "staff_read":
            return request.method in SAFE_METHODS

        # Les autres (staff, admin, etc.) ne sont pas concernés
        return True

    def has_object_permission(self, request, view, obj):
        # Même logique au niveau objet
        user = request.user
        if str(getattr(user, "role", "")).lower() == "staff_read":
            return request.method in SAFE_METHODS
        return True
    
class IsDeclicStaffOrAbove(BasePermission):
    """
    🔒 Autorise l’accès au module Déclic selon le rôle :
      - admin / superadmin → lecture + écriture
      - staff / staff_read → lecture (staff_read lecture seule)
      - declic_staff → lecture + écriture
      - autres → refusé
    """

    message = "Accès réservé au staff Déclic ou supérieur."

    def has_permission(self, request, view):
        u = request.user
        if not u or not u.is_authenticated:
            return False

        # 🔹 Admin / superadmin → accès complet
        if is_admin_like(u):
            return True

        # 🔹 Staff global (staff, staff_read, etc.)
        if is_staff_like(u):
            # staff_read → lecture seule
            if str(getattr(u, "role", "")).lower() == "staff_read":
                return request.method in SAFE_METHODS
            return True

        # 🔹 Staff Déclic → accès complet
        if is_declic_staff(u):
            return True

        # 🔹 Candidats → refusé
        if is_candidate(u):
            self.message = "Les candidats n’ont pas accès à ce module."
            return False

        # 🔹 Par défaut : refus
        return False

class IsPrepaStaffOrAbove(BasePermission):
    """
    🔒 Autorise l’accès au module PrépaComp selon le rôle :
      - admin / superadmin → lecture + écriture
      - staff global → lecture + écriture
      - staff_read → lecture seule
      - prepa_staff → lecture + écriture
      - autres → refusé
    """

    message = "Accès réservé au staff PrépaComp ou supérieur."

    def has_permission(self, request, view):
        u = request.user
        if not u or not u.is_authenticated:
            return False

        if is_admin_like(u):
            return True

        if is_staff_standard(u):
            return True

        if is_prepa_staff(u):
            return True

        if is_staff_read(u):
            return request.method in SAFE_METHODS

        return False

class CanAccessCVTheque(BasePermission):
    """
    Permission CVThèque :
    - Ajoute has_permission() pour éviter les 401
    - has_object_permission() gère preview / download
    - Ajout de logs DEBUG pour comprendre les décisions
    """

    message = "Accès refusé."

    # ===================================================================
    # 🔥 IMPORTANT : has_permission (évite les 401)
    # ===================================================================
    def has_permission(self, request, view):
        u = request.user

        print("\n=== [CVTHEQUE][has_permission] ===")
        print("USER:", getattr(u, "email", None))
        print("AUTHENTICATED:", u.is_authenticated if u else None)
        print("ACTION:", getattr(view, "action", None))
        print("METHOD:", request.method)
        print("=================================\n")

        # Auth obligatoire
        return bool(u and u.is_authenticated)

    # ===================================================================
    # 🔥 Décision finale sur l'objet
    # ===================================================================
    def has_object_permission(self, request, view, obj):
        u = request.user

        print("\n=== [CVTHEQUE][has_object_permission] ===")
        print("USER:", getattr(u, "email", None))
        print("ROLE:", getattr(u, "role", None))
        print("ACTION:", getattr(view, "action", None))
        print("METHOD:", request.method)
        print("OBJ:", obj)
        print("=========================================\n")

        if not u or not u.is_authenticated:
            return False

        # Détection preview/download
        is_preview = getattr(view, "action", None) == "preview"
        is_download = getattr(view, "action", None) == "download"
        is_readonly = request.method in SAFE_METHODS or is_preview or is_download

        cand = obj.candidat
        form = getattr(cand, "formation", None)

        # ===================================================================
        # 🔥 ADMIN / SUPERADMIN → accès total
        # ===================================================================
        if is_admin_like(u):
            print("→ ACCESS GRANTED: admin_like")
            return True

        # ===================================================================
        # 🟦 STAFF_READ → lecture seule dans son périmètre
        # ===================================================================
        if is_staff_read(u):
            ok = (
                is_readonly
                and form
                and form.centre_id in staff_centre_ids(u)
            )
            print("STAFF_READ →", ok)
            return ok

        # ===================================================================
        # 🟩 STAFF → lecture + écriture dans son périmètre
        # ===================================================================
        if is_staff_like(u):
            centres = staff_centre_ids(u)
            if centres is None:
                print("STAFF (ADMIN-LIKE) → accès total")
                return True
            ok = form and form.centre_id in centres
            print("STAFF → centre match ?", ok)
            return ok

        # ===================================================================
        # 🟨 CANDIDAT → uniquement ses documents
        # ===================================================================
        if is_candidate(u):
            ok = cand and cand.compte_utilisateur_id == u.id
            print("CANDIDAT →", ok)
            return ok

        # ===================================================================
        # ⚪ AUTRES RÔLES → lecture seule si créateur ou owner
        # ===================================================================
        if is_readonly:
            ok = (
                getattr(obj, "created_by_id", None) == u.id
                or (cand and cand.compte_utilisateur_id == u.id)
            )
            print("OTHER (READONLY) →", ok)
            return ok

        print("→ ACCESS DENIED")
        return False