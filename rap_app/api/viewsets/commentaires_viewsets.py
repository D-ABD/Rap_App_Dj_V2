# views/commentaire_viewset.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from ..serializers.commentaires_serializers import CommentaireSerializer
from ...models.commentaires import Commentaire

class CommentaireViewSet(viewsets.ModelViewSet):
    """
    API ViewSet pour les commentaires..
    Cette vue permet aux utilisateurs authentifiés de :
    - lister tous les commentaires (GET)
    - créer un nouveau commentaire (POST)
    - consulter un commentaire spécifique (GET)
    - mettre à jour un commentaire (PUT/PATCH)
    - supprimer un commentaire (DELETE)

    Le filtrage par formation ou utilisateur peut être facilement ajouté via query params.
    """
    queryset = Commentaire.objects.all().select_related("utilisateur", "formation")
    serializer_class = CommentaireSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """
        Lors de la création d’un commentaire, associer automatiquement l’utilisateur connecté
        si ce n’est pas explicitement défini (optionnel).
        """
        if not serializer.validated_data.get("utilisateur"):
            serializer.save(utilisateur=self.request.user)
        else:
            serializer.save()
