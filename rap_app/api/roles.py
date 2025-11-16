# -------------------------------------------------------------------
# 🎯 roles.py — version cohérente avec CustomUser
# -------------------------------------------------------------------

def is_candidate(u) -> bool:
    """Vrai si utilisateur est candidat ou stagiaire."""
    return bool(
        getattr(u, "is_authenticated", False)
        and hasattr(u, "is_candidat_or_stagiaire")
        and callable(u.is_candidat_or_stagiaire)
        and u.is_candidat_or_stagiaire()
    )


# -------------------------------------------------------------------
# 👥 Staff & sous-rôles
# -------------------------------------------------------------------

def is_staff_read(u) -> bool:
    """Vrai si utilisateur est staff en lecture seule."""
    return bool(
        u and u.is_authenticated
        and str(getattr(u, "role", "")).lower() == "staff_read"
    )


def is_staff_standard(u) -> bool:
    """Vrai si utilisateur est staff complet."""
    return bool(
        u and u.is_authenticated
        and str(getattr(u, "role", "")).lower() == "staff"
    )


def is_staff_or_staffread(u) -> bool:
    """Vrai si utilisateur est staff complet ou lecture seule."""
    role = str(getattr(u, "role", "")).lower()
    return bool(
        u and u.is_authenticated and role in {"staff", "staff_read"}
    )


# -------------------------------------------------------------------
# 🧑‍💼 Admin / Superadmin
# -------------------------------------------------------------------

def is_admin_like(u) -> bool:
    """Vrai si utilisateur est admin ou superadmin."""
    return bool(
        u and u.is_authenticated
        and (
            getattr(u, "is_superuser", False)
            or str(getattr(u, "role", "")).lower() in {"admin", "superadmin"}
        )
    )


def is_staff_like(u) -> bool:
    """
    Regroupe les rôles de type staff global :
    - staff / staff_read
    - admin / superadmin
    """
    return bool(
        u and u.is_authenticated and (
            is_admin_like(u)
            or is_staff_standard(u)
            or is_staff_read(u)
        )
    )


# -------------------------------------------------------------------
# 🎯 Rôles liés à Déclic et PrépaComp
# -------------------------------------------------------------------

def is_declic_staff(u) -> bool:
    """Vrai si utilisateur est staff spécialisé Déclic (lecture globale + écriture limitée)."""
    return bool(
        u and u.is_authenticated
        and str(getattr(u, "role", "")).lower() == "declic_staff"
    )


def is_prepa_staff(u) -> bool:
    """Vrai si utilisateur est staff spécialisé PrépaComp."""
    return bool(
        u and u.is_authenticated
        and str(getattr(u, "role", "")).lower() == "prepa_staff"
    )


# -------------------------------------------------------------------
# ⚙️ Utilitaires
# -------------------------------------------------------------------

def staff_centre_ids(u):
    """Retourne les IDs de centres accessibles pour un staff (None si admin)."""
    if is_admin_like(u):
        return None
    if is_staff_like(u) or is_prepa_staff(u) or is_declic_staff(u):
        try:
            return list(u.centres.values_list("id", flat=True))
        except Exception:
            return []
    return []


def role_of(u) -> str:
    """Retourne un libellé simple du rôle pour debug/logs."""
    if not u or not getattr(u, "is_authenticated", False):
        return "anonymous"
    role = str(getattr(u, "role", "")).lower()
    if is_admin_like(u): return "admin"
    if is_declic_staff(u): return "declic_staff"
    if is_prepa_staff(u): return "prepa_staff"
    if is_staff_read(u): return "staff_read"
    if is_staff_standard(u): return "staff"
    if is_candidate(u): return "candidate"
    return role or "other"
