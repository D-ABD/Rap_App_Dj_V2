# apps/.../api/roles.py

def is_candidate(u) -> bool:
    """Vrai si utilisateur est candidat/stagiaire."""
    return bool(
        getattr(u, "is_authenticated", False)
        and hasattr(u, "is_candidat_or_stagiaire")
        and callable(u.is_candidat_or_stagiaire)
        and u.is_candidat_or_stagiaire()
    )


def is_staff_or_staffread(u) -> bool:
    """Staff → accès complet, staff_read → lecture seule."""
    role = str(getattr(u, "role", "")).lower()
    return bool(
        u and u.is_authenticated
        and (
            getattr(u, "is_staff", False)
            or role == "staff_read"
        )
    )


def is_admin_like(u) -> bool:
    """Admin-like : superuser ou rôle admin/superadmin."""
    return bool(
        u and u.is_authenticated
        and (
            getattr(u, "is_superuser", False)
            or getattr(u, "is_admin", lambda: False)()
            or str(getattr(u, "role", "")).lower() in {"admin", "superadmin"}
        )
    )


def is_staff_like(u) -> bool:
    """Staff-like : staff, admin, superadmin, staff_read."""
    return bool(
        u and u.is_authenticated
        and (
            getattr(u, "is_staff", False)
            or is_admin_like(u)
            or is_staff_or_staffread(u)
        )
    )


def staff_centre_ids(u):
    """Retourne les IDs de centres accessibles pour un staff (None si admin)."""
    if is_admin_like(u):
        return None
    if is_staff_or_staffread(u):
        try:
            return list(u.centres.values_list("id", flat=True))
        except Exception:
            return []
    return []


def role_of(u) -> str:
    """Retourne un libellé simple du rôle pour debug/logs."""
    if is_candidate(u):
        return "candidate"
    if is_admin_like(u):
        return "admin"
    if is_staff_like(u):
        return "staff"
    return "other"
