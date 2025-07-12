from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse

from ..serializers.formations_serializers import FormationListSerializer

from ...models.formations import Formation
from ...models.commentaires import Commentaire
from ...models.centres import Centre
from ...models.custom_user import CustomUser
from ...models.types_offre import TypeOffre
from ...models.statut import Statut
from ...models.partenaires import Partenaire

from ..serializers.commentaires_serializers import CommentaireSerializer
from ..serializers.centres_serializers import CentreSerializer
from ..serializers.login_logout_serializers import UserSerializer
from ..serializers.types_offre_serializers import TypeOffreSerializer
from ..serializers.statut_serializers import StatutSerializer
from ..serializers.partenaires_serializers import PartenaireSerializer


class SmallPagination(PageNumberPagination):
    page_size = 5
    page_query_param = "page"


@extend_schema(
    summary="🔍 Recherche globale",
    description="""
Recherche un mot-clé dans les objets suivants :
- Formations (nom, numéro d’offre), avec filtres (type_offre, centre, statut)
- Commentaires (contenu)
- Centres (nom)
- Utilisateurs (nom, prénom, username)
- Statuts (nom ou description_autre)
- Types d’offre (nom ou autre)
- Partenaires (nom)
""",
    parameters=[
        OpenApiParameter(name="q", required=True, type=str, description="Mot-clé à rechercher"),
        OpenApiParameter(name="page", required=False, type=int, description="Pagination indépendante par ressource"),
        OpenApiParameter(name="type_offre", required=False, type=int, description="Filtrer les formations par type d'offre"),
        OpenApiParameter(name="statut", required=False, type=int, description="Filtrer les formations par statut"),
        OpenApiParameter(name="centre", required=False, type=int, description="Filtrer les formations par centre"),
    ],
    tags=["Recherche"],
    responses={
        200: OpenApiResponse(
            description="Résultats paginés par ressource",
            examples=[
                OpenApiExample(
                    "Exemple",
                    value={
                        "formations": {"count": 1, "results": [{"id": 1, "nom": "BTS Bio"}]},
                        "commentaires": {"count": 2, "results": [{"id": 7, "contenu": "Bon accueil"}]},
                        "centres": {"count": 1, "results": [{"id": 3, "nom": "Lyon"}]},
                        "utilisateurs": {"count": 1, "results": [{"id": 2, "first_name": "Alice"}]},
                        "types_offre": {"count": 1, "results": [{"id": 5, "nom": "initiale", "autre": ""}]},
                        "statuts": {"count": 1, "results": [{"id": 4, "nom": "pleine", "description_autre": ""}]},
                        "partenaires": {"count": 1, "results": [{"id": 9, "nom": "Mission locale"}]},
                    }
                )
            ]
        )
    }
)
class SearchView(APIView):
    """
    🔍 Vue API pour la recherche globale multi-ressources.

    - Supporte pagination indépendante par ressource
    - Filtres secondaires pour les formations
    - Gère les valeurs personnalisées pour statuts et types d’offres
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if not query:
            return Response({"error": "Paramètre 'q' requis"}, status=400)

        # Filtres secondaires sur les formations
        filtre_type = request.query_params.get("type_offre")
        filtre_statut = request.query_params.get("statut")
        filtre_centre = request.query_params.get("centre")

        response = {}

        def paginate_and_serialize(qs, serializer_class):
            paginator = SmallPagination()
            page = paginator.paginate_queryset(qs, request)
            return paginator.get_paginated_response(serializer_class(page, many=True).data).data

        # Formations (avec filtres)
        formations = Formation.objects.filter(
            Q(nom__icontains=query) | Q(num_offre__icontains=query)
        )
        if filtre_type:
            formations = formations.filter(type_offre_id=filtre_type)
        if filtre_statut:
            formations = formations.filter(statut_id=filtre_statut)
        if filtre_centre:
            formations = formations.filter(centre_id=filtre_centre)

        response["formations"] = paginate_and_serialize(formations, FormationListSerializer)

        # Commentaires
        response["commentaires"] = paginate_and_serialize(
            Commentaire.objects.filter(Q(contenu__icontains=query)),
            CommentaireSerializer
        )

        # Centres
        response["centres"] = paginate_and_serialize(
            Centre.objects.filter(Q(nom__icontains=query)),
            CentreSerializer
        )

        # Utilisateurs
        response["utilisateurs"] = paginate_and_serialize(
            CustomUser.objects.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(username__icontains=query)
            ),
            UserSerializer
        )

        # Types d’offre : nom technique ou "autre"
        response["types_offre"] = paginate_and_serialize(
            TypeOffre.objects.filter(
                Q(nom__icontains=query) | Q(autre__icontains=query)
            ),
            TypeOffreSerializer
        )

        # Statuts : clé ou description_autre
        response["statuts"] = paginate_and_serialize(
            Statut.objects.filter(
                Q(nom__icontains=query) | Q(description_autre__icontains=query)
            ),
            StatutSerializer
        )

        # Partenaires
        response["partenaires"] = paginate_and_serialize(
            Partenaire.objects.filter(Q(nom__icontains=query)),
            PartenaireSerializer
        )

        return Response(response)
