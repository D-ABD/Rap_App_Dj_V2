import csv
import logging
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import (
    OpenApiTypes, extend_schema, OpenApiParameter, OpenApiResponse
)
from django_filters.rest_framework import DjangoFilterBackend
import django_filters

from ...models.documents import Document
from ...models.logs import LogUtilisateur
from ...api.serializers.documents_serializers import (
    DocumentSerializer,
    TypeDocumentChoiceSerializer,
)
from ...api.paginations import RapAppPagination
from ...api.permissions import IsOwnerOrStaffOrAbove

logger = logging.getLogger("application.api")

class DocumentFilter(django_filters.FilterSet):
    centre_id = django_filters.NumberFilter(field_name='formation__centre_id')
    statut_id = django_filters.NumberFilter(field_name='formation__statut_id')
    type_offre_id = django_filters.NumberFilter(field_name='formation__type_offre_id')

    class Meta:
        model = Document
        fields = ['centre_id', 'statut_id', 'type_offre_id']
        
@extend_schema(tags=["Documents"])
class DocumentViewSet(viewsets.ModelViewSet):
    """
    📎 ViewSet complet pour gérer les documents liés aux formations.

    Fonctionnalités :
    - CRUD complet
    - Filtres : centre, statut, type d'offre (via `DocumentFilter`)
    - Export CSV
    - Endpoint par formation
    - Types de documents disponibles
    """
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated & IsOwnerOrStaffOrAbove]
    pagination_class = RapAppPagination

    filter_backends = [DjangoFilterBackend]
    filterset_class = DocumentFilter
    
    @extend_schema(
        summary="📄 Lister tous les documents",
        responses={200: OpenApiResponse(response=DocumentSerializer(many=True))}
    )
    def list(self, request, *args, **kwargs):
        """
        📄 Liste paginée des documents, avec filtres `centre_id`, `statut_id`, `type_offre_id`.
        """
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="📂 Détail d’un document",
        responses={200: OpenApiResponse(response=DocumentSerializer)}
    )
    def retrieve(self, request, *args, **kwargs):
        """
        📂 Détail enrichi d’un document.
        """
        doc = self.get_object()
        serializer = self.get_serializer(doc)
        return Response({
            "success": True,
            "message": "Document récupéré avec succès.",
            "data": serializer.data
        })

    @extend_schema(
        summary="➕ Ajouter un document",
        request=DocumentSerializer,
        responses={201: OpenApiResponse(response=DocumentSerializer)}
    )
    def create(self, request, *args, **kwargs):
        """
        ➕ Création d’un nouveau document.
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            document = serializer.save(created_by=request.user)

            LogUtilisateur.log_action(
                instance=document,
                user=request.user,
                action=LogUtilisateur.ACTION_CREATE,
                details=f"Ajout du document « {document.nom_fichier} »"
            )

            return Response({
                "success": True,
                "message": "Document créé avec succès.",
                "data": document.to_serializable_dict()
            }, status=status.HTTP_201_CREATED)

        logger.warning(f"[API] Erreur création document : {serializer.errors}")
        return Response({
            "success": False,
            "message": "Échec de la création du document.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="✏️ Modifier un document",
        request=DocumentSerializer,
        responses={200: OpenApiResponse(response=DocumentSerializer)}
    )
    def update(self, request, *args, **kwargs):
        """
        ✏️ Mise à jour partielle d’un document.
        """
        instance = self.get_object()
        data = request.data.copy()

        # Ne pas supprimer le fichier s’il n’est pas envoyé
        if 'fichier' not in data or data.get('fichier') in [None, '', 'null']:
            data.pop('fichier', None)

        serializer = self.get_serializer(instance, data=data, partial=True)
        if serializer.is_valid():
            document = serializer.save()

            LogUtilisateur.log_action(
                instance=document,
                user=request.user,
                action=LogUtilisateur.ACTION_UPDATE,
                details=f"Mise à jour du document « {document.nom_fichier} »"
            )

            return Response({
                "success": True,
                "message": "Document mis à jour avec succès.",
                "data": document.to_serializable_dict()
            }, status=status.HTTP_200_OK)

        return Response({
            "success": False,
            "message": "Erreur de validation.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="🗑️ Supprimer un document",
        responses={204: OpenApiResponse(description="Document supprimé avec succès.")}
    )
    def destroy(self, request, *args, **kwargs):
        """
        🗑️ Suppression physique d’un document.
        """
        document = self.get_object()
        document.delete(user=request.user)

        LogUtilisateur.log_action(
            instance=document,
            user=request.user,
            action=LogUtilisateur.ACTION_DELETE,
            details=f"Suppression du document « {document.nom_fichier} »"
        )

        return Response({
            "success": True,
            "message": "Document supprimé avec succès.",
            "data": None
        }, status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="📚 Lister les documents d’une formation",
        parameters=[
            OpenApiParameter(name="formation", type=int, required=True, location="query", description="ID de la formation")
        ],
        responses={200: OpenApiResponse(response=DocumentSerializer(many=True))}
    )
    @action(detail=False, methods=["get"], url_path="par-formation")
    def par_formation(self, request):
        """
        📚 Retourne tous les documents liés à une formation donnée.
        """
        formation_id = request.query_params.get("formation")
        if not formation_id:
            return Response({"success": False, "message": "Paramètre 'formation' requis."}, status=400)

        try:
            formation_id = int(formation_id)
        except ValueError:
            return Response({"success": False, "message": "ID de formation invalide."}, status=400)

        queryset = self.queryset.filter(formation_id=formation_id)
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page or queryset, many=True)
        return self.get_paginated_response(serializer.data) if page else Response({
            "success": True,
            "data": serializer.data
        })

    @extend_schema(
        summary="🧾 Exporter tous les documents au format CSV",
        responses={
            200: OpenApiResponse(
                description="Fichier CSV contenant la liste des documents",
                response=OpenApiTypes.BINARY
            )
        }
    )
    @action(detail=False, methods=["get"], url_path="export-csv")
    def export_csv(self, request):
        """
        🧾 Export CSV complet des documents (non filtré).
        """
        response = HttpResponse(content_type='text/csv')
        response["Content-Disposition"] = "attachment; filename=documents.csv"

        writer = csv.writer(response)
        writer.writerow(["ID", "Nom", "Type", "Formation", "Auteur", "Taille (Ko)", "MIME"])

        for doc in self.queryset:
            writer.writerow([
                doc.id,
                doc.nom_fichier,
                doc.get_type_document_display(),
                doc.formation.nom if doc.formation else "",
                str(doc.created_by) if doc.created_by else "",
                doc.taille_fichier or "",
                doc.mime_type or ""
            ])

        return response

    @extend_schema(
        summary="Liste des types de documents",
        description="Retourne les types de documents valides avec leurs libellés lisibles.",
        tags=["Documents"],
        responses={200: OpenApiResponse(response=TypeDocumentChoiceSerializer(many=True))}
    )
    @action(detail=False, methods=["get"], url_path="types", url_name="types")
    def get_types(self, request):
        """
        📋 Retourne les types de documents disponibles.
        """
        data = [
            {"value": value, "label": label}
            for value, label in Document.TYPE_DOCUMENT_CHOICES
        ]
        serializer = TypeDocumentChoiceSerializer(data, many=True)
        return Response({
            "success": True,
            "message": "Types de documents disponibles.",
            "data": serializer.data
        })

    @extend_schema(
        summary="Récupérer les filtres disponibles pour les documents",
        responses={200: OpenApiResponse(description="Filtres disponibles")}
    )
    @action(detail=False, methods=["get"], url_path="filtres")
    def get_filtres(self, request):
        """
        Renvoie les options de filtres disponibles pour les documents.
        ⚠️ Affiche uniquement les centres/statuts/types liés à au moins un document.
        """
        centres = Document.objects \
            .filter(formation__centre__isnull=False) \
            .values_list("formation__centre_id", "formation__centre__nom") \
            .distinct()

        statuts = Document.objects \
            .filter(formation__statut__isnull=False) \
            .values_list("formation__statut_id", "formation__statut__nom") \
            .distinct()

        type_offres = Document.objects \
            .filter(formation__type_offre__isnull=False) \
            .values_list("formation__type_offre_id", "formation__type_offre__nom") \
            .distinct()

        return Response({
            "success": True,
            "message": "Filtres documents récupérés avec succès",
            "data": {
                "centres": [{"id": c[0], "nom": c[1]} for c in centres],
                "statuts": [{"id": s[0], "nom": s[1]} for s in statuts],
                "type_offres": [{"id": t[0], "nom": t[1]} for t in type_offres],
            }
        })
