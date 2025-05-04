# IsOwnerOrStaffOrAbove

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from ..serializers.documents_serializers import DocumentSerializer
from ...models.documents import Document
from ..permissions import IsOwnerOrStaffOrAbove


@extend_schema(
    tags=["Documents"],
    summary="Gérer les documents de formation",
    description="""
        Ce ViewSet permet :
        - aux utilisateurs : d'accéder à leurs propres documents,
        - aux membres `staff`, `admin`, `superadmin` : d’accéder à tous les documents.

        Le champ `utilisateur` est automatiquement renseigné à la création.
    """
)
class DocumentViewSet(viewsets.ModelViewSet):
    """
    API ViewSet pour les documents liés aux formations.

    Accès :
    - GET : liste/détail des documents accessibles
    - POST/PUT/PATCH/DELETE : création/modification/suppression d’un document

    Permissions :
    - L’utilisateur peut accéder uniquement à ses documents
    - Les rôles staff/admin/superadmin ont un accès complet
    """

    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrStaffOrAbove]

    def get_queryset(self):
        user = self.request.user
        role = getattr(user.profile, "role", "")

        if role in ["staff", "admin", "superadmin"]:
            return Document.objects.all().select_related('formation', 'utilisateur')
        return Document.objects.filter(utilisateur=user).select_related('formation', 'utilisateur')

    def perform_create(self, serializer):
        """
        Associe automatiquement l'utilisateur connecté au document.
        """
        serializer.save(utilisateur=self.request.user)
