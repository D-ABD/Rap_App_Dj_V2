from rest_framework import viewsets
from ..mixins import StaffCentresScopeMixin, UserVisibilityScopeMixin
from ..permissions import IsStaffReadOrAbove
from ..paginations import RapAppPagination


class BaseScopedViewSet(
    StaffCentresScopeMixin,
    UserVisibilityScopeMixin,
    viewsets.ModelViewSet,
):
    """
    Base ViewSet pour toutes les vues scoppées par centre/département/utilisateur.

    Règles d’accès appliquées automatiquement :
      - Admin / Superadmin : accès global
      - Staff : accès restreint à ses centres/départements
      - Staff_read : lecture seule sur ce périmètre
      - Candidat / Stagiaire : accès uniquement à ses objets (via user_visibility_lookups)

    À surcharger dans les ViewSets concrets :
      - queryset ou get_queryset()  (⚠️ get_queryset doit appeler super())
      - serializer_class
      - centre_lookups / departement_lookups si la relation centre est indirecte
      - user_visibility_lookups si l’objet est lié à un utilisateur autrement que par created_by
    """

    # 🔹 Permissions globales
    permission_classes = [IsStaffReadOrAbove]

    # 🔹 Pagination par défaut
    pagination_class = RapAppPagination

    # 🔹 Config par défaut des mixins
    centre_lookups = ("centre_id",)
    departement_lookups = ("centre__code_postal",)
    user_visibility_lookups = ("created_by",)
    include_staff = False  # staff/staff_read sont gérés par StaffCentresScopeMixin
