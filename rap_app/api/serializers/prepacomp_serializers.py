from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from django.utils.translation import gettext_lazy as _

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError

from ...models.prepacomp import Semaine, PrepaCompGlobal


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name="Exemple de semaine",
            value={
                "centre": {"id": 1, "nom": "Centre de Paris"},
                "annee": 2025,
                "mois": 5,
                "numero_semaine": 20,
                "date_debut_semaine": "2025-05-12",
                "date_fin_semaine": "2025-05-18",
                "objectif_annuel_prepa": 250,
                "objectif_mensuel_prepa": 80,
                "objectif_hebdo_prepa": 20,
                "nombre_places_ouvertes": 15,
                "nombre_prescriptions": 18,
                "nombre_presents_ic": 14,
                "nombre_adhesions": 12,
                "departements": {"75": 5, "92": 7},
                "nombre_par_atelier": {"AT1": 6, "AT3": 6}
            },
            response_only=False
        )
    ]
)
class SemaineSerializer(serializers.ModelSerializer):
    """
    📅 Serializer principal pour les objets Semaine.
    Fournit une sortie enrichie via `to_serializable_dict`.
    """

    class Meta:
        model = Semaine
        fields = [
            "id", "centre", "annee", "mois", "numero_semaine",
            "date_debut_semaine", "date_fin_semaine",
            "objectif_annuel_prepa", "objectif_mensuel_prepa", "objectif_hebdo_prepa",
            "nombre_places_ouvertes", "nombre_prescriptions", "nombre_presents_ic",
            "nombre_adhesions", "departements", "nombre_par_atelier",
            "created_at", "updated_at", "created_by", "updated_by", "is_active"
        ]
        read_only_fields = ["id", "created_at", "updated_at", "created_by", "updated_by", "is_active"]
        extra_kwargs = {
            "centre": {
                "help_text": "Centre de formation concerné"
            },
            "annee": {
                "help_text": "Année de la semaine"
            },
            "mois": {
                "help_text": "Mois de la semaine (1-12)"
            },
            "numero_semaine": {
                "help_text": "Numéro de la semaine dans l’année"
            },
            "date_debut_semaine": {
                "help_text": "Premier jour de la semaine"
            },
            "date_fin_semaine": {
                "help_text": "Dernier jour de la semaine"
            },
            "objectif_annuel_prepa": {
                "help_text": "Objectif annuel de préparation pour le centre"
            },
            "objectif_mensuel_prepa": {
                "help_text": "Objectif mensuel de préparation pour le mois concerné"
            },
            "objectif_hebdo_prepa": {
                "help_text": "Objectif hebdomadaire de préparation"
            },
            "nombre_places_ouvertes": {
                "help_text": "Nombre de places ouvertes cette semaine"
            },
            "nombre_prescriptions": {
                "help_text": "Nombre de prescriptions reçues cette semaine"
            },
            "nombre_presents_ic": {
                "help_text": "Nombre de personnes présentes en information collective"
            },
            "nombre_adhesions": {
                "help_text": "Nombre total d'adhésions réalisées"
            },
            "departements": {
                "help_text": "Répartition des adhésions par code département"
            },
            "nombre_par_atelier": {
                "help_text": "Répartition des participants par atelier (AT1–AT6)"
            },
        }

    def to_representation(self, instance):
        return {
            "success": True,
            "message": "Semaine récupérée avec succès.",
            "data": instance.to_serializable_dict(),
        }

    def validate(self, data):
        """
        Valide les règles de cohérence métier définies dans .clean()
        """
        instance = Semaine(**data)
        try:
            instance.full_clean()
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict)
        return data


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name="Exemple de bilan global",
            value={
                "centre": {"id": 1, "nom": "Centre de Lyon"},
                "annee": 2025,
                "adhesions": 120,
                "presents": 150,
                "taux_transformation": 80.0,
                "taux_objectif_annee": 60.0,
                "objectif_annuel_prepa": 200,
                "objectif_hebdo": 20,
                "prescriptions": 180,
                "places_ouvertes": 130,
                "objectif_restant": 80,
                "semaines_restantes": 30,
                "adhesions_hebdo_necessaires": 2.7,
                "moyenne_hebdomadaire": 4.5,
                "objectif_jury": {
                    "annuel": 40,
                    "mensuel": 10
                }
            },
            response_only=False
        )
    ]
)
class PrepaCompGlobalSerializer(serializers.ModelSerializer):
    """
    📊 Serializer principal pour PrepaCompGlobal.
    Utilise `to_serializable_dict` pour l’API.
    """

    class Meta:
        model = PrepaCompGlobal
        fields = [
            "id", "centre", "annee", "total_candidats", "total_prescriptions",
            "adhesions", "total_presents", "total_places_ouvertes",
            "objectif_annuel_prepa", "objectif_hebdomadaire_prepa",
            "objectif_annuel_jury", "objectif_mensuel_jury",
            "created_at", "updated_at", "created_by", "updated_by", "is_active"
        ]
        read_only_fields = ["id", "created_at", "updated_at", "created_by", "updated_by", "is_active"]
        extra_kwargs = {
            "centre": {
                "help_text": "Centre de formation concerné"
            },
            "annee": {
                "help_text": "Année de référence pour le bilan"
            },
            "total_candidats": {
                "help_text": "Total des candidats cumulés sur l’année"
            },
            "total_prescriptions": {
                "help_text": "Total des prescriptions enregistrées"
            },
            "adhesions": {
                "help_text": "Nombre total d’adhésions"
            },
            "total_presents": {
                "help_text": "Nombre de personnes présentes en information collective"
            },
            "total_places_ouvertes": {
                "help_text": "Nombre total de places ouvertes"
            },
            "objectif_annuel_prepa": {
                "help_text": "Objectif annuel de préparation"
            },
            "objectif_hebdomadaire_prepa": {
                "help_text": "Objectif hebdomadaire de préparation"
            },
            "objectif_annuel_jury": {
                "help_text": "Objectif annuel pour les jurys"
            },
            "objectif_mensuel_jury": {
                "help_text": "Objectif mensuel pour les jurys"
            },
        }

    def to_representation(self, instance):
        return {
            "success": True,
            "message": "Statistiques PrépaComp récupérées avec succès.",
            "data": instance.to_serializable_dict(),
        }
