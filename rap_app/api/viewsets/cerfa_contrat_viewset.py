import os
from django.http import FileResponse, Http404
from django.conf import settings
from django.core.exceptions import ValidationError
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from ...models.cerfa_contrats import CerfaContrat
from ..serializers.cerfa_contrat_serializer import CerfaContratSerializer
from ...utils.pdf_cerfa_utils import generer_pdf_cerfa


class CerfaContratViewSet(viewsets.ModelViewSet):
    """
    API CRUD pour les contrats CERFA d’apprentissage.
    Gère les erreurs de validation, les champs manquants et la génération PDF.
    """

    queryset = CerfaContrat.objects.all().select_related("candidat", "formation", "employeur")
    serializer_class = CerfaContratSerializer
    permission_classes = []  # 👉 à adapter à ton système d’authentification

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["candidat", "formation", "employeur", "diplome_vise", "auto_generated"]
    search_fields = ["apprenti_nom_naissance", "apprenti_prenom", "employeur_nom"]
    ordering_fields = ["created_at", "date_conclusion", "date_debut_execution"]
    ordering = ["-created_at"]

    # ───────────────────────────────
    # 🔹 CREATE — simple, fiable, serializer cohérent
    # ───────────────────────────────
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            cerfa = serializer.save()
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        headers = self.get_success_headers(serializer.data)
        # On renvoie le contrat complet (avec missing_fields calculé)
        data = self.get_serializer(cerfa, context={"request": request}).data
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)

    # ───────────────────────────────
    # 🔹 UPDATE — idem, sans logique redondante
    # ───────────────────────────────
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        try:
            cerfa = serializer.save()
        except ValidationError as e: 
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = self.get_serializer(cerfa, context={"request": request}).data
        return Response(data, status=status.HTTP_200_OK)
 
    # ───────────────────────────────
    # 🔹 Génération du PDF (avec fallback automatique)
    # ───────────────────────────────
    @action(detail=True, methods=["post"], url_path="generate-pdf")
    def generate_pdf(self, request, pk=None):
        """Génère le PDF CERFA et l’associe à l’objet.
        Si le modèle officiel ne peut pas être rempli, utilise un PDF simplifié.
        """
        from ...utils.pdf_cerfa_utils import generer_pdf_cerfa, generer_pdf_cerfa_simple

        # ⚙️ On recharge le contrat avec toutes ses relations
        cerfa = self.get_queryset().select_related("formation", "employeur", "candidat").get(pk=pk)
        flatten = request.query_params.get("flatten", "false").lower() in ("1", "true", "yes")

        try:
            cerfa.populate_auto()  # 🔄 complète les infos manquantes

            try:
                # 🧩 Tentative avec le CERFA officiel interactif
                pdf_path = generer_pdf_cerfa(cerfa, flatten=flatten)
            except Exception as e:
                # ⚠️ Si erreur (modèle introuvable ou non interactif)
                (f"[WARN] Impossible de générer le CERFA officiel : {e}")
                pdf_path = generer_pdf_cerfa_simple(cerfa)

            # 💾 Sauvegarde du chemin relatif dans le modèle
            rel_path = os.path.relpath(pdf_path, start=settings.MEDIA_ROOT)
            cerfa.pdf_fichier.name = rel_path
            cerfa.save(update_fields=["pdf_fichier"])

        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Erreur de génération du PDF : {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = self.get_serializer(cerfa, context={"request": request})
        return Response(
            {
                "message": f"✅ PDF généré avec succès (flatten={flatten})",
                "id": cerfa.id,
                "pdf_url": serializer.data.get("pdf_url"),
            },
            status=status.HTTP_200_OK,
        )

    # ───────────────────────────────
    # 🔹 Téléchargement du PDF
    # ───────────────────────────────
    @action(detail=True, methods=["get"], url_path="download-pdf")
    def download_pdf(self, request, pk=None):
        """Télécharge le fichier PDF CERFA (le génère s’il n’existe pas)."""
        cerfa = self.get_object()
        if not cerfa.pdf_fichier or not os.path.exists(cerfa.pdf_fichier.path):
            pdf_path = generer_pdf_cerfa(cerfa)
            rel_path = os.path.relpath(pdf_path, start=settings.MEDIA_ROOT)
            cerfa.pdf_fichier.name = rel_path
            cerfa.save(update_fields=["pdf_fichier"])

        pdf_path = cerfa.pdf_fichier.path
        if not os.path.exists(pdf_path):
            raise Http404("Le fichier PDF est introuvable.")

        filename = f"cerfa_{cerfa.id}.pdf"
        response = FileResponse(open(pdf_path, "rb"), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
       
    # ───────────────────────────────
    # 🔹 Accès direct au PDF (affichage navigateur)
    # ───────────────────────────────
    @action(detail=True, methods=["get"], url_path="pdf")
    def view_pdf(self, request, pk=None):
        """Affiche le PDF directement dans le navigateur (inline).
        Génère le PDF s’il n’existe pas encore.
        """
        cerfa = self.get_object()

        # (Re)génère si nécessaire
        if not cerfa.pdf_fichier or not os.path.exists(cerfa.pdf_fichier.path):
            pdf_path = generer_pdf_cerfa(cerfa)
            rel_path = os.path.relpath(pdf_path, start=settings.MEDIA_ROOT)
            cerfa.pdf_fichier.name = rel_path
            cerfa.save(update_fields=["pdf_fichier"])

        pdf_path = cerfa.pdf_fichier.path
        if not os.path.exists(pdf_path):
            raise Http404("Le fichier PDF est introuvable.")

        # 🔸 Affiche dans le navigateur (pas de téléchargement direct)
        filename = f"cerfa_{cerfa.id}.pdf"
        response = FileResponse(open(pdf_path, "rb"), content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{filename}"'
        return response


    # ───────────────────────────────
    # 🔹 Dernier contrat d’un candidat
    # ───────────────────────────────
    @action(detail=False, methods=["get"], url_path="latest")
    def latest_by_candidat(self, request):
        """Retourne le dernier CERFA d’un candidat donné."""
        candidat_id = request.query_params.get("candidat")
        if not candidat_id:
            return Response({"error": "Paramètre ?candidat= requis"}, status=400)

        cerfa = (
            CerfaContrat.objects.filter(candidat_id=candidat_id)
            .order_by("-created_at")
            .first()
        )
        if not cerfa:
            return Response({"detail": "Aucun CERFA trouvé pour ce candidat"}, status=404)

        serializer = self.get_serializer(cerfa, context={"request": request})
        return Response(serializer.data)

    # ───────────────────────────────
    # 🔹 Liste des CERFA auto-générés
    # ───────────────────────────────
    @action(detail=False, methods=["get"], url_path="auto-generated")
    def list_auto_generated(self, request):
        """Retourne uniquement les CERFA auto_generated=True."""
        queryset = self.filter_queryset(self.get_queryset().filter(auto_generated=True))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)

    # ───────────────────────────────
    # 🔹 Tous les CERFA d’un candidat
    # ───────────────────────────────
    @action(detail=False, methods=["get"], url_path=r"by-candidat/(?P<candidat_id>\d+)")
    def list_by_candidat(self, request, candidat_id=None):
        """Retourne tous les CERFA liés à un candidat donné."""
        queryset = self.filter_queryset(self.get_queryset().filter(candidat_id=candidat_id))
        if not queryset.exists():
            return Response({"detail": "Aucun CERFA trouvé pour ce candidat"}, status=404)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)
 