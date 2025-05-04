# IsOwnerOrStaffOrAbove

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from ..serializers.commentaires_serializers import CommentaireSerializer
from ...models.commentaires import Commentaire
from ..permissions import IsOwnerOrStaffOrAbove


@extend_schema(
    tags=["Commentaires"],
    summary="Gérer les commentaires de formation",
    description="""
        Cette vue permet :
        - aux utilisateurs : d'accéder à leurs propres commentaires,
        - aux rôles staff/admin/superadmin : d'accéder à tous les commentaires.

        L'utilisateur est automatiquement associé au commentaire qu’il crée s’il n’est pas spécifié.
    """
)
class CommentaireViewSet(viewsets.ModelViewSet):
    """
    API ViewSet pour les commentaires.

    Actions disponibles :
    - GET /commentaires/        : liste des commentaires accessibles
    - GET /commentaires/{id}/   : détail
    - POST /commentaires/       : création
    - PUT/PATCH /commentaires/{id}/ : modification
    - DELETE /commentaires/{id}/ : suppression

    Permissions :
    - L'utilisateur peut gérer ses propres commentaires.
    - Le staff, admin, superadmin peuvent gérer tous les commentaires.
    """

    serializer_class = CommentaireSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrStaffOrAbove]

    def get_queryset(self):
        """
        Restreint la liste selon le rôle :
        - superadmin/admin/staff : tous les commentaires
        - utilisateur standard : seulement les siens
        """
        user = self.request.user
        role = getattr(user.profile, "role", "")

        if role in ["staff", "admin", "superadmin"]:
            return Commentaire.objects.all().select_related("utilisateur", "formation")
        return Commentaire.objects.filter(utilisateur=user).select_related("utilisateur", "formation")

    def perform_create(self, serializer):
        """
        Lors de la création d’un commentaire, associer automatiquement l’utilisateur connecté
        s’il n’est pas explicitement défini.
        """
        if not serializer.validated_data.get("utilisateur"):
            serializer.save(utilisateur=self.request.user)
        else:
            serializer.save()
