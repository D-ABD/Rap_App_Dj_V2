git add rap_app/api/serializers/documents_serializers.py \
        rap_app/api/viewsets/documents_viewsets.py \
        rap_app/models/documents.py

git commit -m "feat(documents): amélioration du DocumentViewSet et ajout des métadonnées temporelles

- Ajout de created_at et updated_at dans DocumentSerializer
- Mise à jour de BaseModel.to_serializable_dict() pour inclure updated_at
- Refonte de get_filtres (ajout formations, simplification)
- Amélioration de download (headers et encodage)
- Harmonisation du format de réponse API"

git push origin main
