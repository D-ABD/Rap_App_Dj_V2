import csv
import logging
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from ...models.formations import Formation
from ...api.serializers.formations_serializers import FormationSerializer
from ...api.paginations import RapAppPagination
from ...api.permissions import ReadWriteAdminReadStaff

logger = logging.getLogger("application.api")


@extend_schema(tags=["Formations"])
class FormationViewSet(viewsets.ModelViewSet):
    """
    📚 ViewSet pour gérer les formations.
    Inclut les opérations CRUD, l'historique, les documents, les commentaires, les prospections,
    ainsi que des actions personnalisées comme duplication et export CSV.
    """
    queryset = Formation.objects.all()
    serializer_class = FormationSerializer
    permission_classes = [IsAuthenticated & ReadWriteAdminReadStaff]
    pagination_class = RapAppPagination

    @extend_schema(
        summary="Lister les formations",
        description="Retourne une liste paginée des formations avec filtres disponibles.",
        tags=["Formations"],
        parameters=[
            OpenApiParameter("texte", str, description="Recherche texte libre (nom, commentaire...)"),
            OpenApiParameter("type_offre", str, description="ID du type d'offre"),
            OpenApiParameter("centre", str, description="ID du centre"),
            OpenApiParameter("statut", str, description="ID du statut"),
            OpenApiParameter("date_debut", str, description="Date de début minimale (AAAA-MM-JJ)"),
            OpenApiParameter("date_fin", str, description="Date de fin maximale (AAAA-MM-JJ)"),
            OpenApiParameter("places_disponibles", str, description="Filtre les formations avec des places disponibles"),
            OpenApiParameter("tri", str, description="Champ de tri (ex: -start_date, nom...)"),
        ],
        responses={200: OpenApiResponse(response=FormationSerializer(many=True))}
    )
    def list(self, request, *args, **kwargs):
        params = request.query_params
        queryset = Formation.objects.recherche(
            texte=params.get("texte"),
            type_offre=params.get("type_offre"),
            centre=params.get("centre"),
            statut=params.get("statut"),
            date_debut=params.get("date_debut"),
            date_fin=params.get("date_fin"),
            places_disponibles=params.get("places_disponibles") == "true"
        )
        if tri := params.get("tri"):
            queryset = Formation.objects.trier_par(tri)

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page or queryset, many=True)
        return self.get_paginated_response(serializer.data) if page else Response(serializer.data)

    @extend_schema(
        summary="Détail d'une formation",
        tags=["Formations"],
        responses={200: OpenApiResponse(response=FormationSerializer)}
    )
    def retrieve(self, request, *args, **kwargs):
        return Response(self.get_object().to_serializable_dict())

    @extend_schema(
        summary="Créer une formation",
        tags=["Formations"],
        request=FormationSerializer,
        responses={201: FormationSerializer}
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            formation = serializer.save()
            return Response(
                {
                    "success": True,
                    "message": "Formation créée avec succès.",
                    "data": formation.to_serializable_dict()
                },
                status=status.HTTP_201_CREATED
            )
        logger.warning(f"[API] Erreur création formation : {serializer.errors}")
        return Response(
            {
                "success": False,
                "message": "Erreur de validation.",
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    @extend_schema(
        summary="Mettre à jour une formation",
        tags=["Formations"],
        request=FormationSerializer,
        responses={200: FormationSerializer}
    )
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            formation = serializer.save()
            return Response(
                {
                    "success": True,
                    "message": "Formation mise à jour avec succès.",
                    "data": formation.to_serializable_dict()
                },
                status=status.HTTP_200_OK
            )
        logger.warning(f"[API] Erreur mise à jour formation : {serializer.errors}")
        return Response(
            {
                "success": False,
                "message": "Erreur de validation.",
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    @extend_schema(summary="Obtenir l'historique d'une formation", tags=["Formations"])
    @action(detail=True, methods=["get"])
    def historique(self, request, pk=None):
        data = [h.to_serializable_dict() for h in self.get_object().get_historique()]
        return Response({"success": True, "data": data})

    @extend_schema(summary="Lister les partenaires d'une formation", tags=["Formations"])
    @action(detail=True, methods=["get"])
    def partenaires(self, request, pk=None):
        data = [p.to_serializable_dict() for p in self.get_object().get_partenaires()]
        return Response({"success": True, "data": data})

    @extend_schema(summary="Lister les commentaires d'une formation", tags=["Formations"])
    @action(detail=True, methods=["get"])
    def commentaires(self, request, pk=None):
        f = self.get_object()
        limit = request.query_params.get("limit")
        with_saturation = request.query_params.get("saturation") == "true"
        qs = f.get_commentaires(include_saturation=with_saturation, limit=int(limit) if limit else None)
        return Response({"success": True, "data": [c.to_serializable_dict() for c in qs]})

    @extend_schema(summary="Lister les documents d'une formation", tags=["Formations"])
    @action(detail=True, methods=["get"])
    def documents(self, request, pk=None):
        est_public = request.query_params.get("est_public")
        est_public = est_public.lower() == "true" if est_public is not None else None
        docs = self.get_object().get_documents(est_public)
        return Response({"success": True, "data": [d.to_serializable_dict() for d in docs]})

    @extend_schema(summary="Lister les prospections liées à une formation", tags=["Formations"])
    @action(detail=True, methods=["get"])
    def prospections(self, request, pk=None):
        prosps = self.get_object().get_prospections()
        return Response({"success": True, "data": [p.to_serializable_dict() for p in prosps]})

    @extend_schema(summary="Ajouter un commentaire à une formation", tags=["Formations"])
    @action(detail=True, methods=["post"])
    def ajouter_commentaire(self, request, pk=None):
        try:
            c = self.get_object().add_commentaire(
                user=request.user,
                contenu=request.data.get("contenu"),
                saturation=request.data.get("saturation")
            )
            return Response({"success": True, "data": c.to_serializable_dict()})
        except Exception as e:
            logger.exception("Ajout commentaire échoué")
            return Response({"success": False, "message": str(e)}, status=400)

    @extend_schema(summary="Ajouter un événement à une formation", tags=["Formations"])
    @action(detail=True, methods=["post"])
    def ajouter_evenement(self, request, pk=None):
        try:
            e = self.get_object().add_evenement(
                type_evenement=request.data.get("type_evenement"),
                event_date=request.data.get("event_date"),
                details=request.data.get("details"),
                description_autre=request.data.get("description_autre"),
                user=request.user
            )
            return Response({"success": True, "data": e.to_serializable_dict()})
        except Exception as e:
            logger.exception("Ajout événement échoué")
            return Response({"success": False, "message": str(e)}, status=400)

    @extend_schema(summary="Ajouter un document à une formation", tags=["Formations"])
    @action(detail=True, methods=["post"])
    def ajouter_document(self, request, pk=None):
        try:
            doc = self.get_object().add_document(
                user=request.user,
                fichier=request.FILES.get("fichier"),
                nom_fichier=request.data.get("nom_fichier"),
                type_document=request.data.get("type_document")
            )
            return Response({"success": True, "data": doc.to_serializable_dict()})
        except Exception as e:
            logger.exception("Ajout document échoué")
            return Response({"success": False, "message": str(e)}, status=400)

    @extend_schema(summary="Dupliquer une formation", tags=["Formations"])
    @action(detail=True, methods=["post"])
    def dupliquer(self, request, pk=None):
        try:
            f = self.get_object().duplicate(user=request.user)
            return Response({"success": True, "message": "Formation dupliquée", "data": f.to_serializable_dict()})
        except Exception as e:
            logger.exception("Duplication échouée")
            return Response({"success": False, "message": str(e)}, status=400)

    @extend_schema(summary="Exporter les formations au format CSV", tags=["Formations"])
    @action(detail=False, methods=["get"])
    def export_csv(self, request):
        formations = Formation.objects.all()
        response = HttpResponse(content_type='text/csv')
        response["Content-Disposition"] = "attachment; filename=formations.csv"
        writer = csv.writer(response)
        writer.writerow(Formation.get_csv_headers())
        for f in formations:
            writer.writerow(f.to_csv_row())
        return response

    @extend_schema(summary="Statistiques mensuelles des formations", tags=["Formations"])
    @action(detail=False, methods=["get"])
    def stats_par_mois(self, request):
        annee = request.query_params.get("annee")
        stats = Formation.get_stats_par_mois(annee=annee)
        return Response({"success": True, "data": stats})
