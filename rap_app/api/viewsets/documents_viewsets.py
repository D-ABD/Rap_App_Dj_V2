import csv
import logging
import mimetypes
import urllib.parse
from django.http import HttpResponse, FileResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import (
    OpenApiTypes, extend_schema, OpenApiParameter, OpenApiResponse
)
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import PermissionDenied
import django_filters


from ...models.documents import Document
from ...models.logs import LogUtilisateur
from ...api.serializers.documents_serializers import (
    DocumentSerializer,
    TypeDocumentChoiceSerializer,
)
from ...api.paginations import RapAppPagination
from ...api.permissions import IsStaffOrAbove, is_staff_or_staffread  # ✅ staff/admin/superadmin only

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

    ⚠️ Scope centres :
      - Admin/Superadmin : accès global
      - Staff : limité aux documents dont la formation appartient à ses centres
    """
    serializer_class = DocumentSerializer
    permission_classes = [IsStaffOrAbove]
    pagination_class = RapAppPagination

    filter_backends = [DjangoFilterBackend]
    filterset_class = DocumentFilter

    # --------------------- helpers scope/permissions ---------------------

    def _is_admin_like(self, user) -> bool:
        return getattr(user, "is_superuser", False) or (hasattr(user, "is_admin") and user.is_admin())

    def _staff_centre_ids(self, user):
        """Liste des centres du staff (None si admin-like = accès global)."""
        if self._is_admin_like(user):
            return None
        if is_staff_or_staffread(user):
            # nécessite le M2M user.centres (déjà ajouté)
            return list(user.centres.values_list("id", flat=True))
        return []

    def _scope_qs_to_user_centres(self, qs):
        """Applique le scope par centres au queryset."""
        user = self.request.user
        centre_ids = self._staff_centre_ids(user)
        if centre_ids is None:
            return qs  # admin/superadmin
        if centre_ids:
            return qs.filter(formation__centre_id__in=centre_ids)
        return qs.none()

    def _assert_staff_can_use_formation(self, formation):
        """Empêche un staff d'écrire hors de son périmètre (centre de la formation)."""
        if not formation:
            return
        user = self.request.user
        if self._is_admin_like(user):
            return
        if is_staff_or_staffread(user):
            allowed = set(user.centres.values_list("id", flat=True))
            if getattr(formation, "centre_id", None) not in allowed:
                raise PermissionDenied("Formation hors de votre périmètre (centre).")

    # ------------------------------ queryset ------------------------------

    def get_queryset(self):
        base = (
            Document.objects
            .select_related("formation", "formation__centre", "formation__statut", "formation__type_offre", "created_by")
            .all()
        )
        return self._scope_qs_to_user_centres(base)

    # ------------------------------ list/retrieve -------------------------

    @extend_schema(
        summary="📄 Lister tous les documents",
        responses={200: OpenApiResponse(response=DocumentSerializer(many=True))}
    )
    def list(self, request, *args, **kwargs):
        """📄 Liste paginée des documents, avec filtres `centre_id`, `statut_id`, `type_offre_id`."""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="📂 Détail d’un document",
        responses={200: OpenApiResponse(response=DocumentSerializer)}
    )
    def retrieve(self, request, *args, **kwargs):
        """📂 Détail enrichi d’un document."""
        doc = self.get_object()  # get_object() utilise get_queryset() -> scopé
        serializer = self.get_serializer(doc)
        return Response({
            "success": True,
            "message": "Document récupéré avec succès.",
            "data": serializer.data
        })

    # ------------------------------ create/update/destroy -----------------

    @extend_schema(
        summary="➕ Ajouter un document",
        request=DocumentSerializer,
        responses={201: OpenApiResponse(response=DocumentSerializer)}
    )
    def create(self, request, *args, **kwargs):
        """➕ Création d’un nouveau document."""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # contrôle périmètre avant save
            formation = serializer.validated_data.get("formation")
            self._assert_staff_can_use_formation(formation)

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
        """✏️ Mise à jour partielle d’un document."""
        instance = self.get_object()
        data = request.data.copy()

        # Ne pas supprimer le fichier s’il n’est pas envoyé
        if 'fichier' not in data or data.get('fichier') in [None, '', 'null']:
            data.pop('fichier', None)

        serializer = self.get_serializer(instance, data=data, partial=True)
        if serializer.is_valid():
            # contrôle périmètre (nouvelle formation si fournie, sinon formation existante)
            new_formation = serializer.validated_data.get("formation", instance.formation)
            self._assert_staff_can_use_formation(new_formation)

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
        """🗑️ Suppression physique d’un document."""
        document = self.get_object()
        # verrouille la suppression au périmètre centre
        self._assert_staff_can_use_formation(getattr(document, "formation", None))

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

    # ------------------------------ actions custom ------------------------

    @extend_schema(
        summary="📚 Lister les documents d’une formation",
        parameters=[
            OpenApiParameter(name="formation", type=int, required=True, location="query", description="ID de la formation")
        ],
        responses={200: OpenApiResponse(response=DocumentSerializer(many=True))}
    )
    @action(detail=False, methods=["get"], url_path="par-formation")
    def par_formation(self, request):
        """📚 Retourne tous les documents liés à une formation donnée (scopé)."""
        formation_id = request.query_params.get("formation")
        if not formation_id:
            return Response({"success": False, "message": "Paramètre 'formation' requis."}, status=400)

        try:
            formation_id = int(formation_id)
        except ValueError:
            return Response({"success": False, "message": "ID de formation invalide."}, status=400)

        queryset = self.get_queryset().filter(formation_id=formation_id)
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page or queryset, many=True)
        return self.get_paginated_response(serializer.data) if page else Response({
            "success": True,
            "data": serializer.data
        })

    @extend_schema(
        summary="🧾 Exporter tous les documents au format CSV (scopé + filtré)",
        responses={
            200: OpenApiResponse(
                description="Fichier CSV contenant la liste des documents",
                response=OpenApiTypes.BINARY
            )
        }
    )
    @action(detail=False, methods=["get"], url_path="export-csv")
    def export_csv(self, request):
        """🧾 Export CSV des documents selon filtres + scope centres."""
        qs = self.filter_queryset(self.get_queryset())

        response = HttpResponse(content_type='text/csv')
        response["Content-Disposition"] = "attachment; filename=documents.csv"

        writer = csv.writer(response)
        writer.writerow(["ID", "Nom", "Type", "Formation", "Auteur", "Taille (Ko)", "MIME"])

        for doc in qs:
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
        """📋 Retourne les types de documents disponibles."""
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
        summary="Récupérer les filtres disponibles pour les documents (scopé)",
        responses={200: OpenApiResponse(description="Filtres disponibles")}
    )
    @action(detail=False, methods=["get"], url_path="filtres")
    def get_filtres(self, request):
        """
        Renvoie les options de filtres disponibles pour les documents.
        ⚠️ Affiche uniquement les centres/statuts/types/formations liés à au moins un document,
        et uniquement dans le périmètre de l'utilisateur.
        """
        scoped = self.get_queryset()

        centres = scoped \
            .filter(formation__centre__isnull=False) \
            .values_list("formation__centre_id", "formation__centre__nom") \
            .distinct()

        statuts = scoped \
            .filter(formation__statut__isnull=False) \
            .values_list("formation__statut_id", "formation__statut__nom") \
            .distinct()

        type_offres = scoped \
            .filter(formation__type_offre__isnull=False) \
            .values_list("formation__type_offre_id", "formation__type_offre__nom") \
            .distinct()

        # ✅ Liste des formations liées à des documents
        formations = scoped \
            .filter(formation__isnull=False) \
            .values_list(
                "formation__id",
                "formation__nom",
                "formation__num_offre",
                "formation__type_offre__nom",
            ) \
            .distinct() \
            .order_by("formation__nom")

        return Response({
            "success": True,
            "message": "Filtres documents récupérés avec succès",
            "data": {
                "centres": [{"id": c[0], "nom": c[1]} for c in centres],
                "statuts": [{"id": s[0], "nom": s[1]} for s in statuts],
                "type_offres": [{"id": t[0], "nom": t[1]} for t in type_offres],
                # ✅ Ajout du filtre formation (compatibilité front)
                "formations": [
                    {
                        "id": f[0],
                        "nom": f[1],
                        "num_offre": f[2],
                        "type_offre_nom": f[3],
                        "type_offre_libelle": f[3],  # même valeur pour compat front
                    }
                    for f in formations
                ],
            }
        })



    @extend_schema(
        summary="⬇️ Télécharger un document",
        description="Permet de télécharger directement le fichier du document (avec Content-Disposition).",
        responses={200: OpenApiResponse(response=OpenApiTypes.BINARY)},
    )
    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, pk=None):
        """
        Téléchargement direct du fichier associé au document.
        Retourne une vraie réponse fichier (FileResponse) avec les bons headers HTTP.
        """
        doc = self.get_object()

        # 🔒 Vérifie qu’un fichier existe
        if not doc.fichier:
            return Response(
                {"success": False, "message": "Aucun fichier associé à ce document."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 📂 Ouvre le fichier en lecture binaire
        try:
            file_handle = doc.fichier.open("rb")
        except FileNotFoundError:
            return Response(
                {"success": False, "message": "Fichier introuvable sur le serveur."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 🧠 Détermine le type MIME
        mime_type, _ = mimetypes.guess_type(doc.fichier.name)
        mime_type = mime_type or "application/octet-stream"

        # 📤 Crée la réponse
        response = FileResponse(file_handle, content_type=mime_type)

        # 🔠 Encode proprement le nom du fichier pour tous les navigateurs
        filename = urllib.parse.quote(doc.nom_fichier or doc.fichier.name)
        response["Content-Disposition"] = f"attachment; filename*=UTF-8''{filename}"

        # 🚫 Évite la mise en cache pour les fichiers sensibles
        response["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response["Pragma"] = "no-cache"
        response["Expires"] = "0"

        return response
