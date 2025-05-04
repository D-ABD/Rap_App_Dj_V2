from rest_framework import viewsets, permissions

from ..serializers.documents_serializers import DocumentSerializer
from ...models.documents import Document

class DocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les documents associés aux formations.

    Permet :
    - GET /documents/ : Liste des documents
    - GET /documents/<id>/ : Détail d’un document
    - POST /documents/ : Créer un nouveau document
    - PUT/PATCH /documents/<id>/ : Modifier un document
    - DELETE /documents/<id>/ : Supprimer un document

    🔐 Permissions :
    - Lecture : Authentification requise
    - Écriture : Authentification requise
    """
    queryset = Document.objects.all().select_related('formation', 'utilisateur')
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """
        Associe l'utilisateur connecté comme créateur du document.
        """
        serializer.save(utilisateur=self.request.user)
