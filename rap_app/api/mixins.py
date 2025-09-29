from typing import Optional, Tuple
from django.db.models import Q, QuerySet


class StaffCentresScopeMixin:
    """
    Restreint le queryset au périmètre staff :
      - Admin/Superadmin : accès global (pas de filtre).
      - Staff : limité aux centres ET/OU départements auxquels il est affecté.
      - Staff_read : idem staff mais lecture seule (géré par la permission).
      - Non-staff : aucun résultat (si jamais les permissions laissaient passer).

    Personnalisation par ViewSet :
      - centre_lookups: chemins vers l'ID centre (ex: ("centre_id",) ou ("formation__centre_id",))
      - departement_lookups: chemins vers un champ "code postal" ou "code departement"
                             (ex: ("centre__code_postal",) ou ("centre__departement_code",))
      - departement_code_len: longueur du préfixe à matcher (défaut 2 → "92", "75", ...)

    Récupération du périmètre staff :
      - Centres : via M2M `user.centres` (par défaut)
      - Départements : via `departements_codes` ou `departements` (user ou user.profile)
    """

    # ---- config par défaut (override dans les ViewSets si nécessaire) ----
    centre_lookups: Tuple[str, ...] = ("centre_id",)
    departement_lookups: Tuple[str, ...] = ("centre__code_postal",)
    departement_code_len: int = 2

    staff_centres_attr: str = "centres"
    staff_departements_attrs: Tuple[str, ...] = ("departements_codes", "departements")

    # ---- helpers ----
    def _is_admin_like(self, u) -> bool:
        return bool(
            getattr(u, "is_superuser", False)
            or (hasattr(u, "is_admin") and callable(u.is_admin) and u.is_admin())
        )

    def _is_staff_or_read(self, u) -> bool:
        """True si staff classique ou staff_read"""
        if not u:
            return False
        return getattr(u, "is_staff", False) or getattr(u, "role", "") == "staff_read"

    def _user_centre_ids(self) -> Optional[list[int]]:
        """
        Retourne la liste d'IDs de centres visibles par l'utilisateur staff.
        - None => accès global (admin/superadmin)
        - []   => staff sans centre : aucun résultat via centres (peut être compensé par les départements)
        """
        u = self.request.user
        if self._is_admin_like(u):
            return None
        if self._is_staff_or_read(u):
            centres_rel = getattr(u, self.staff_centres_attr, None)
            if hasattr(centres_rel, "values_list"):
                return list(centres_rel.values_list("id", flat=True))
            return []
        return []

    def _user_departement_codes(self) -> Optional[list[str]]:
        """
        Retourne la liste des codes département (ex: ["92","75"]) pour l'utilisateur staff/staff_read.
        - None => accès global (admin/superadmin)
        - []   => pas de scope département
        """
        u = self.request.user
        if self._is_admin_like(u):
            return None
        if not self._is_staff_or_read(u):
            return []

        # chercher sur user puis user.profile
        for owner in (u, getattr(u, "profile", None)):
            if not owner:
                continue
            for attr in self.staff_departements_attrs:
                val = getattr(owner, attr, None)
                if val is None:
                    continue

                # M2M vers un modèle avec champ "code"
                if hasattr(val, "all"):
                    codes = []
                    try:
                        for obj in val.all():
                            code = getattr(obj, "code", None) or str(obj)
                            if code:
                                codes.append(str(code)[: self.departement_code_len])
                    except Exception:
                        pass
                    if codes:
                        return list(set(codes))

                # liste/tuple/set
                if isinstance(val, (list, tuple, set)):
                    codes = [
                        str(x)[: self.departement_code_len]
                        for x in val
                        if x is not None and str(x).strip() != ""
                    ]
                    if codes:
                        return list(set(codes))

                # string unique
                s = str(val).strip()
                if s:
                    return [s[: self.departement_code_len]]

        return []

    def scope_queryset_to_centres(self, qs: QuerySet):
        """
        Applique le scope staff/staff_read:
          (centre_lookups IN centre_ids) OR (departement_lookups STARTSWITH dep_code)
        """
        ids = self._user_centre_ids()
        dep_codes = self._user_departement_codes()

        # accès global si admin-like (ids==None ou dep_codes==None)
        if ids is None or dep_codes is None:
            return qs

        if not ids and not dep_codes:
            return qs.none()

        q = Q()

        if ids:
            q_centres = Q()
            for path in self.centre_lookups:
                q_centres |= Q(**{f"{path}__in": ids})
            q |= q_centres

        if dep_codes:
            q_deps = Q()
            for path in self.departement_lookups:
                for code in dep_codes:
                    q_deps |= Q(**{f"{path}__startswith": code})
            q |= q_deps

        return qs.filter(q).distinct()

    # hook DRF
    def get_queryset(self):
        base = super().get_queryset()
        return self.scope_queryset_to_centres(base)

class UserVisibilityScopeMixin:
    """
    Restreint le queryset aux objets appartenant à l'utilisateur connecté (non staff/admin).
    - Admin/Superadmin : accès global.
    - Staff/Staff_read : pas de filtrage ici (c’est StaffCentresScopeMixin qui gère).
    - Non-staff (candidat/stagiaire) : applique un filtre OR sur `user_visibility_lookups`.

    Exemple d’utilisation dans un ViewSet :
      class MyViewSet(StaffCentresScopeMixin, UserVisibilityScopeMixin, ModelViewSet):
          user_visibility_lookups = ("created_by", "prospections__owner")
    """

    user_visibility_lookups: Tuple[str, ...] = ("created_by",)
    include_staff: bool = False

    def _is_admin_like(self, u) -> bool:
        return bool(
            getattr(u, "is_superuser", False)
            or (hasattr(u, "is_admin") and callable(u.is_admin) and u.is_admin())
        )

    def _build_q_from_lookups(self, user) -> Q:
        q = Q()
        for path in self.user_visibility_lookups:
            leaf = path.split("__")[-1]
            if leaf.endswith("_id"):
                q |= Q(**{path: user.id})
            else:
                q |= Q(**{path: user})
        return q

    def user_visibility_q(self, user) -> Q:
        return self._build_q_from_lookups(user)

    def scope_queryset_to_user_visibility(self, qs: QuerySet):
        user = self.request.user
        if not (user and user.is_authenticated):
            return qs.none()

        if self._is_admin_like(user):
            return qs

        # Staff et staff_read → laissé à StaffCentresScopeMixin
        if (getattr(user, "is_staff", False) or getattr(user, "role", "") == "staff_read") and not self.include_staff:
            return qs

        return qs.filter(self.user_visibility_q(user)).distinct()

    def get_queryset(self):
        base = super().get_queryset()
        return self.scope_queryset_to_user_visibility(base)