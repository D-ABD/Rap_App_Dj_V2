from datetime import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from ..serializers.prepacomp_serializers import PrepaCompGlobalSerializer, SemaineSerializer
from ...models.prepacomp import PrepaCompGlobal, Semaine


class SemaineViewSet(viewsets.ModelViewSet):
    """
    API permettant de consulter, créer et mettre à jour les données hebdomadaires (Semaine).
    """
    queryset = Semaine.objects.all().select_related("centre")
    serializer_class = SemaineSerializer

    @action(detail=False, methods=["get"])
    def stats_par_annee(self, request):
        """
        Statistiques par atelier pour une année complète.
        URL : /api/semaine/stats_par_annee/?annee=2024
        """
        annee = int(request.query_params.get("annee", timezone.now().year))
        data = Semaine.stats_globales_par_atelier(annee)
        return Response(data)


class PrepaCompGlobalViewSet(viewsets.ModelViewSet):
    """
    API pour accéder aux bilans globaux PrépaComp par centre.
    """
    queryset = PrepaCompGlobal.objects.all().select_related("centre")
    serializer_class = PrepaCompGlobalSerializer

    @action(detail=False, methods=["get"])
    def objectifs(self, request):
        """
        Retourne les objectifs par centre pour l’année spécifiée.
        URL : /api/prepacompglobal/objectifs/?annee=2024
        """
        annee = int(request.query_params.get("annee", timezone.now().year))
        data = PrepaCompGlobal.objectifs_par_centre(annee)
        return Response(data)

    @action(detail=False, methods=["get"])
    def stats_mensuelles(self, request):
        """
        Retourne les statistiques mensuelles globales (ou par centre).
        URL : /api/prepacompglobal/stats_mensuelles/?annee=2024&centre_id=1
        """
        annee = int(request.query_params.get("annee", timezone.now().year))
        centre_id = request.query_params.get("centre_id")

        if centre_id:
            from rap_app_project.rap_app.models.centres import Centre
            try:
                centre = Centre.objects.get(pk=centre_id)
            except Centre.DoesNotExist:
                return Response({"detail": "Centre non trouvé."}, status=status.HTTP_404_NOT_FOUND)
        else:
            centre = None

        data = PrepaCompGlobal.stats_par_mois(annee, centre)
        return Response(data)
