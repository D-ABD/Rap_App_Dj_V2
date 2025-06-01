import csv
import logging
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import OpenApiTypes

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from ...models.documents import Document
from ...models.logs import LogUtilisateur
from ...api.serializers.documents_serializers import DocumentSerializer, TypeDocumentChoiceSerializer
from ...api.paginations import RapAppPagination
from ...api.permissions import IsOwnerOrStaffOrAbove

logger = logging.getLogger("application.api")


@extend_schema(tags=["Documents"])
class DocumentViewSet(viewsets.ModelViewSet):
    """
    📎 ViewSet complet pour gérer les documents liés aux formations.
    """
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated & IsOwnerOrStaffOrAbove]
    pagination_class = RapAppPagination

    @extend_schema(
        summary="📄 Lister tous les documents",
        responses={200: OpenApiResponse(response=DocumentSerializer(many=True))}
    )
    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.queryset)
        serializer = self.get_serializer(page or self.queryset, many=True)
        return self.get_paginated_response(serializer.data) if page else Response({
            "success": True,
            "message": "Liste des documents.",
            "data": serializer.data
        })

    @extend_schema(
        summary="📂 Détail d’un document",
        responses={200: OpenApiResponse(response=DocumentSerializer)}
    )
    def retrieve(self, request, *args, **kwargs):
        doc = self.get_object()
        return Response({
            "success": True,
            "message": "Document récupéré avec succès.",
            "data": doc.to_serializable_dict()
        })

    @extend_schema(
        summary="➕ Ajouter un document",
        request=DocumentSerializer,
        responses={201: OpenApiResponse(response=DocumentSerializer)}
    )
    def create(self, request, *args, **kwargs):
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
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)

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

