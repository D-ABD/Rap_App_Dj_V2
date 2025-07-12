import io
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from rest_framework.exceptions import ValidationError
from django.http import Http404
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4


from ...models.commentaires import Commentaire
from ...models.logs import LogUtilisateur
from ...api.serializers.commentaires_serializers import CommentaireMetaSerializer, CommentaireSerializer
from ...api.paginations import RapAppPagination
from ...api.permissions import IsOwnerOrStaffOrAbove
from ...utils.exporter import Exporter

 
@extend_schema(tags=["Commentaires"])
class CommentaireViewSet(viewsets.ModelViewSet):
    """
    API CRUD pour les commentaires liés aux formations.
    Permet la création, l’édition, la suppression, la recherche et l’export.
    """
    queryset = Commentaire.objects.select_related(
        "formation", "formation__type_offre", "formation__statut", "created_by"
    ).all()
    serializer_class = CommentaireSerializer
    pagination_class = RapAppPagination
    permission_classes = [IsOwnerOrStaffOrAbove]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["contenu", "formation__nom", "formation__num_offre", "created_by__username"]
    ordering = ["-created_at"]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["include_full_content"] = True
        return context

    @action(detail=False, methods=["get"], url_path="export")
    def export(self, request):
        """
        Export des commentaires en PDF/CSV/Word
        """
        format = request.query_params.get('format', 'pdf')
        ids = request.query_params.get('ids', '')
        export_all = request.query_params.get('all', 'false').lower() == 'true'

        queryset = self.filter_queryset(self.get_queryset())
        
        # Filtre par IDs si spécifié
        if ids:
            id_list = [int(id) for id in ids.split(',') if id.isdigit()]
            queryset = queryset.filter(id__in=id_list)
        
        # Si 'all' n'est pas true et aucun ID spécifié, retourner vide
        if not export_all and not ids:
            return Response({"detail": "Aucun commentaire sélectionné"}, status=400)

        if format == 'pdf':
            return self.export_pdf(queryset)
        elif format == 'csv':
            return self.export_csv(queryset)
        elif format == 'word':
            return self.export_word(queryset)
        else:
            return Response({"detail": "Format non supporté"}, status=400)

    def export_pdf(self, queryset):
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        y = A4[1] - 50  # Position verticale initiale

        for commentaire in queryset:
            if y < 100:  # Nouvelle page si on arrive en bas
                p.showPage()
                y = A4[1] - 50
            
            p.setFont("Helvetica", 10)
            p.drawString(50, y, f"{commentaire.formation_nom} - {commentaire.auteur}")
            y -= 15
            p.drawString(50, y, commentaire.contenu[:100])  # Limite à 100 caractères
            y -= 30

        p.save()
        buffer.seek(0)

        return HttpResponse(
            buffer.read(),
            content_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="commentaires.pdf"'}
        )

    def export_csv(self, queryset):
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="commentaires.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID', 'Formation', 'Auteur', 'Contenu', 'Date'])

        for commentaire in queryset:
            writer.writerow([
                commentaire.id,
                commentaire.formation_nom,
                commentaire.auteur,
                commentaire.contenu,
                commentaire.date
            ])

        return response

    def export_word(self, queryset):
        from docx import Document
        from io import BytesIO

        document = Document()
        document.add_heading('Export des commentaires', 0)

        for commentaire in queryset:
            document.add_paragraph(f"ID: {commentaire.id}", style='Heading2')
            document.add_paragraph(f"Formation: {commentaire.formation_nom}")
            document.add_paragraph(f"Auteur: {commentaire.auteur}")
            document.add_paragraph(f"Date: {commentaire.date}")
            document.add_paragraph(f"Contenu: {commentaire.contenu}")
            document.add_paragraph("-" * 50)

        buffer = BytesIO()
        document.save(buffer)
        buffer.seek(0)

        return HttpResponse(
            buffer.read(),
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": 'attachment; filename="commentaires.docx"'}
        )

    def get_queryset(self):
        """
        Récupère les commentaires en fonction des filtres :
        - formation
        - auteur
        - centre
        - type_offre
        - statut
        - date_min / date_max
        - saturation_min / saturation_max
        - formation_etat : actives / a_venir / terminees / a_recruter
        """
        queryset = Commentaire.objects.select_related(
            "formation", "formation__centre", "formation__type_offre", "formation__statut", "created_by"
        ).all()

        # Filtres basiques
        formation_id = self.request.query_params.get("formation")
        if formation_id:
            queryset = queryset.filter(formation_id=formation_id)

        auteur_id = self.request.query_params.get("auteur")
        if auteur_id:
            queryset = queryset.filter(created_by_id=auteur_id)

        centre_id = self.request.query_params.get("centre_id")
        if centre_id:
            queryset = queryset.filter(formation__centre_id=centre_id)

        statut_id = self.request.query_params.get("statut_id")
        if statut_id:
            queryset = queryset.filter(formation__statut_id=statut_id)

        type_offre_id = self.request.query_params.get("type_offre_id")
        if type_offre_id:
            queryset = queryset.filter(formation__type_offre_id=type_offre_id)

        # Filtres sur la date de création
        date_min = self.request.query_params.get("date_min")
        if date_min:
            queryset = queryset.filter(created_at__date__gte=date_min)

        date_max = self.request.query_params.get("date_max")
        if date_max:
            queryset = queryset.filter(created_at__date__lte=date_max)

        # Filtres sur la saturation (copiée de la formation)
        saturation_min = self.request.query_params.get("saturation_min")
        if saturation_min:
            queryset = queryset.filter(saturation_formation__gte=saturation_min)

        saturation_max = self.request.query_params.get("saturation_max")
        if saturation_max:
            queryset = queryset.filter(saturation_formation__lte=saturation_max)
        
        from ...models.formations import Formation

        # 🎯 Filtre supplémentaire : état de la formation associée
        formation_etat = self.request.query_params.get("formation_etat")
        if formation_etat == "actives":
            queryset = queryset.filter(formation_id__in=Formation.objects.formations_actives().values("id"))
        elif formation_etat == "a_venir":
            queryset = queryset.filter(formation_id__in=Formation.objects.formations_a_venir().values("id"))
        elif formation_etat == "terminees":
            queryset = queryset.filter(formation_id__in=Formation.objects.formations_terminees().values("id"))
        elif formation_etat == "a_recruter":
            queryset = queryset.filter(formation_id__in=Formation.objects.formations_a_recruter().values("id"))

        # 🔍 Log de doublons
        ids = list(queryset.values_list('id', flat=True))
        duplicates = [i for i in set(ids) if ids.count(i) > 1]
        if duplicates:
            print(f"🚨 Doublons Commentaire IDs (x{len(duplicates)}) détectés : {duplicates}")

        # ✅ Supprime les doublons potentiels
        return queryset.distinct()

    @extend_schema(
        summary="Récupérer les filtres disponibles pour les commentaires",
        responses={200: OpenApiResponse(description="Filtres disponibles")}
    )
    @action(detail=False, methods=["get"], url_path="filtres")
    def get_filtres(self, request):
        """
        Renvoie les options de filtres disponibles pour les commentaires.
        """
        centres = Commentaire.objects \
            .filter(formation__centre__isnull=False) \
            .values_list("formation__centre_id", "formation__centre__nom") \
            .distinct()

        statuts = Commentaire.objects \
            .filter(formation__statut__isnull=False) \
            .values_list("formation__statut_id", "formation__statut__nom") \
            .distinct()

        type_offres = Commentaire.objects \
            .filter(formation__type_offre__isnull=False) \
            .values_list("formation__type_offre_id", "formation__type_offre__nom") \
            .distinct()

        formation_etats = [
            {"value": "actives", "label": "Formations actives"},
            {"value": "a_venir", "label": "À venir"},
            {"value": "terminees", "label": "Formations terminées"},
            {"value": "a_recruter", "label": "À recruter"},
        ]

        return Response({
            "success": True,
            "message": "Filtres récupérés avec succès",
            "data": {
                "centres": [{"id": c[0], "nom": c[1]} for c in centres],
                "statuts": [{"id": s[0], "nom": s[1]} for s in statuts],
                "type_offres": [{"id": t[0], "nom": t[1]} for t in type_offres],
                "formation_etats": formation_etats,
            }
        })


    @extend_schema(summary="Lister les commentaires actifs")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Récupérer un commentaire")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="Créer un commentaire")
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        commentaire = serializer.save()

        LogUtilisateur.log_action(
            instance=commentaire,
            action=LogUtilisateur.ACTION_CREATE,
            user=request.user,
            details=f"Création d'un commentaire pour la formation #{commentaire.formation_id}"
        )

        return Response({
            "success": True,
            "message": "Commentaire créé avec succès.",
            "data": commentaire.to_serializable_dict(include_full_content=True)
        }, status=status.HTTP_201_CREATED)

    @extend_schema(summary="Mettre à jour un commentaire")
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        commentaire = serializer.save()

        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_UPDATE,
            user=request.user,
            details=f"Mise à jour du commentaire #{instance.pk}"
        )

        return Response({
            "success": True,
            "message": "Commentaire mis à jour avec succès.",
            "data": commentaire.to_serializable_dict(include_full_content=True)
        }, status=status.HTTP_200_OK)

    @extend_schema(summary="Supprimer un commentaire")
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()

        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_DELETE,
            user=request.user,
            details=f"Suppression du commentaire #{instance.pk}"
        )

        return Response({
            "success": True,
            "message": "Commentaire supprimé avec succès.",
            "data": None
        }, status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="Récupérer les statistiques de saturation des commentaires",
        responses={
            200: OpenApiResponse(
                description="Données de saturation pour une formation",
                response=None
            )
        }
    )
    @action(detail=False, methods=["get"], url_path="saturation-stats")
    def saturation_stats(self, request):
        """
        Renvoie les statistiques de saturation pour une formation donnée.
        """
        formation_id = request.query_params.get("formation_id")
        stats = Commentaire.get_saturation_stats(formation_id=formation_id)

        return Response({
            "success": True,
            "message": "Statistiques de saturation récupérées avec succès.",
            "data": stats
        })








