import csv
import logging
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.views import APIView

from ...utils.filters import HistoriqueFormationFilter

from ...models.formations import Formation, HistoriqueFormation
from ...api.paginations import RapAppPagination
from ...api.permissions import ReadWriteAdminReadStaff
from ...api.serializers.formations_serializers import (
    FormationCreateSerializer,
    FormationListSerializer,
    FormationDetailSerializer,
    HistoriqueFormationSerializer
)

logger = logging.getLogger("application.api")


@extend_schema(tags=["Formations"])
class FormationViewSet(viewsets.ModelViewSet):
    """
    📚 ViewSet pour gérer les formations.
    Inclut les opérations CRUD, l'historique, les documents, les commentaires, les prospections,
    ainsi que des actions personnalisées comme duplication et export CSV.
    """
    queryset = Formation.objects.all()
    permission_classes = [IsAuthenticated & ReadWriteAdminReadStaff]
    pagination_class = RapAppPagination

    def get_serializer_class(self):
        if self.action == "list":
            return FormationListSerializer
        if self.action == "retrieve":
            return FormationDetailSerializer
        if self.action == "create":
            return FormationCreateSerializer  # ✅ ici on valide avec un serializer simplifié
        if self.action in ["update", "partial_update"]:
            return FormationDetailSerializer
        return super().get_serializer_class()

        




    @extend_schema(
        summary="Lister les formations",
        description="Retourne une liste paginée des formations avec filtres disponibles.",
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
        responses={200: OpenApiResponse(response=FormationListSerializer(many=True))}
    )

    @action(detail=False, methods=["get"])
    def filtres(self, request):
        centres = Formation.objects.values_list("centre_id", "centre__nom").distinct()
        statuts = Formation.objects.values_list("statut_id", "statut__nom").distinct()
        type_offres = Formation.objects.values_list("type_offre_id", "type_offre__nom").distinct()

        return Response({
            "success": True,
            "data": {
                "centres": [{"id": c[0], "nom": c[1]} for c in centres if c[0] is not None],
                "statuts": [{"id": s[0], "nom": s[1]} for s in statuts if s[0] is not None],
                "type_offres": [{"id": t[0], "nom": t[1]} for t in type_offres if t[0] is not None],
            }
        })

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

        if page:
            return Response({
                "success": True,
                "message": "Liste paginée des formations",
                "data": {
                    "count": self.paginator.page.paginator.count,
                    "results": serializer.data
                }
            })

        return Response({
            "success": True,
            "message": "Liste complète des formations",
            "data": {
                "count": len(serializer.data),
                "results": serializer.data
            }
        })
    @extend_schema(
    summary="Créer une formation",
    request=FormationDetailSerializer,
    responses={201: FormationDetailSerializer}
)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            formation = serializer.save()

            # Recharge avec les relations nécessaires pour le rendu
            formation = Formation.objects.select_related(
                "centre", "type_offre", "statut"
            ).get(pk=formation.pk)

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
        request=FormationDetailSerializer,
        responses={200: FormationDetailSerializer}
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

    @extend_schema(summary="Obtenir l'historique d'une formation")
    @action(detail=True, methods=["get"])
    def historique(self, request, pk=None):
        data = [h.to_serializable_dict() for h in self.get_object().get_historique()]
        return Response({"success": True, "data": data})

    @extend_schema(summary="Lister les partenaires d'une formation")
    @action(detail=True, methods=["get"])
    def partenaires(self, request, pk=None):
        data = [p.to_serializable_dict() for p in self.get_object().get_partenaires()]
        return Response({"success": True, "data": data})

    @extend_schema(summary="Lister les commentaires d'une formation")
    @action(detail=True, methods=["get"])
    def commentaires(self, request, pk=None):
        f = self.get_object()
        limit = request.query_params.get("limit")
        with_saturation = request.query_params.get("saturation") == "true"
        qs = f.get_commentaires(include_saturation=with_saturation, limit=int(limit) if limit else None)
        return Response({
            "success": True,
            "data": [c.to_serializable_dict(include_full_content=True) for c in qs]
        })

    @extend_schema(summary="Lister les documents d'une formation")
    @action(detail=True, methods=["get"])
    def documents(self, request, pk=None):
        est_public = request.query_params.get("est_public")
        est_public = est_public.lower() == "true" if est_public is not None else None
        docs = self.get_object().get_documents(est_public)
        return Response({"success": True, "data": [d.to_serializable_dict() for d in docs]})

    @extend_schema(summary="Lister les prospections liées à une formation")
    @action(detail=True, methods=["get"])
    def prospections(self, request, pk=None):
        prosps = self.get_object().get_prospections()
        return Response({"success": True, "data": [p.to_serializable_dict() for p in prosps]})

    @extend_schema(summary="Ajouter un commentaire à une formation")
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

    @extend_schema(summary="Ajouter un événement à une formation")
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

    @extend_schema(summary="Ajouter un document à une formation")
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

    @extend_schema(summary="Dupliquer une formation")
    @action(detail=True, methods=["post"])
    def dupliquer(self, request, pk=None):
        try:
            f = self.get_object().duplicate(user=request.user)
            return Response({"success": True, "message": "Formation dupliquée", "data": f.to_serializable_dict()})
        except Exception as e:
            logger.exception("Duplication échouée")
            return Response({"success": False, "message": str(e)}, status=400)

    @extend_schema(summary="Exporter les formations au format CSV")
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

    @extend_schema(summary="Statistiques mensuelles des formations")
    @action(detail=False, methods=["get"])
    def stats_par_mois(self, request):
        annee = request.query_params.get("annee")
        stats = Formation.get_stats_par_mois(annee=annee)
        return Response({"success": True, "data": stats})

    @extend_schema(
        summary="Liste simplifiée des formations (sans pagination)",
        description="Retourne une liste allégée (id, nom, num_offre) de toutes les formations actives, sans pagination."
    )
    @action(detail=False, methods=["get"], url_path="liste-simple")
    def liste_simple(self, request):
        print("👤 Utilisateur :", request.user)
        print("✅ Est admin :", request.user.is_superuser)
        formations = Formation.objects.all().only("id", "nom", "num_offre").order_by("nom")
        data = [
            {"id": f.id, "nom": f.nom, "num_offre": getattr(f, "num_offre", None)}
            for f in formations
        ]
        return Response({"success": True, "data": data})

    @action(detail=False, methods=["get"], url_path="historique")
    def all_historique(self, request):
        """🔁 Retourne l’historique de toutes les formations"""
        historique = HistoriqueFormation.objects.select_related("formation", "created_by").order_by("-created_at")
        serializer = HistoriqueFormationSerializer(historique, many=True)
        return Response({"success": True, "data": serializer.data}, status=status.HTTP_200_OK)

        
@extend_schema(
    tags=["Historique des formations"],
    summary="Lister tous les historiques",
    description="Retourne tous les historiques de modifications (même si la formation n'existe plus)."
)

class HistoriqueFormationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet en lecture seule pour l'historique des formations.

    Permet de rechercher, trier, filtrer, et paginer les modifications
    liées à une formation.
    """
    queryset = HistoriqueFormation.objects.select_related(
        'formation__centre',
        'formation__statut',
        'formation__type_offre',
        'created_by',
        'modified_by'
    ).order_by('-created_at')

    serializer_class = HistoriqueFormationSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = HistoriqueFormationFilter

    ordering_fields = ['created_at', 'champ_modifie']
    search_fields = ['champ_modifie', 'ancienne_valeur', 'nouvelle_valeur']
    pagination_class = RapAppPagination  # ou pagination par défaut de DRF

    def list(self, request, *args, **kwargs):
        print("✅ Query params :", request.query_params)

        queryset = self.filter_queryset(self.get_queryset())

        print("✅ Nombre après filtre :", queryset.count())
        print("✅ Requête SQL :", str(queryset.query))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                "success": True,
                "message": "Historique paginé",
                "data": serializer.data
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "success": True,
            "message": "Historique complet",
            "data": serializer.data,
            "count": len(serializer.data)
        })
    
    def get_queryset(self):
        print("✅ Params reçus :", self.request.query_params)
        return super().get_queryset()

class HistoriqueFormationGroupedView(APIView):
    """
    Vue personnalisée qui retourne l’historique groupé par formation.
    Chaque entrée contient les informations de la formation et ses derniers changements.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        queryset = HistoriqueFormation.objects.select_related(
            'formation__centre',
            'formation__statut',
            'formation__type_offre',
            'created_by',
            'modified_by'
        )

        # 🔍 Appliquer les filtres DRF à la main (car ce n’est pas un ViewSet)
        filtre = HistoriqueFormationFilter(request.GET, queryset=queryset)
        if not filtre.is_valid():
            return Response({
                "success": False,
                "message": "Filtres invalides",
                "errors": filtre.errors
            }, status=400)

        filtered_qs = filtre.qs

        # 🧠 Groupement par formation
        grouped_data = {}
        for obj in filtered_qs:
            fid = obj.formation_id
            formation = obj.formation
            if fid not in grouped_data:
                grouped_data[fid] = {
                    "formation_id": fid,
                    "formation_nom": formation.nom,
                    "centre_nom": formation.centre.nom if formation.centre else "",
                    "type_offre_nom": formation.type_offre.nom if formation.type_offre else "",
                    "type_offre_couleur": formation.type_offre.couleur if formation.type_offre else "",
                    "statut_nom": formation.statut.nom if formation.statut else "",
                    "statut_couleur": formation.statut.couleur if formation.statut else "",
                    "numero_offre": formation.num_offre,
                    "total_modifications": 0,
                    "derniers_historiques": [],
                }

            grouped_data[fid]["total_modifications"] += 1
            if len(grouped_data[fid]["derniers_historiques"]) < 5:
                grouped_data[fid]["derniers_historiques"].append({
                    "id": obj.id,
                    "champ_modifie": obj.champ_modifie,
                    "ancienne_valeur": obj.ancienne_valeur,
                    "nouvelle_valeur": obj.nouvelle_valeur,
                    "commentaire": obj.commentaire,
                    "created_at": obj.created_at,
                })

        return Response({
            "success": True,
            "message": "Historique groupé par formation",
            "data": list(grouped_data.values())
        })
