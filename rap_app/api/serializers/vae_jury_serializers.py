from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from django.utils.translation import gettext_lazy as _

from ...models.vae_jury import VAE, SuiviJury, HistoriqueStatutVAE


# -------------------- Suivi Jury --------------------

@extend_schema_serializer(examples=[
    OpenApiExample(
        name="Exemple Suivi Jury",
        value={
            "centre_id": 1,
            "annee": 2024,
            "mois": 5,
            "objectif_jury": 10,
            "jurys_realises": 8
        }
    )
])
class SuiviJurySerializer(serializers.ModelSerializer):
    centre_nom = serializers.CharField(source="centre.nom", read_only=True)
    mois_libelle = serializers.CharField(source="get_mois_display", read_only=True)
    periode = serializers.CharField(source="get_periode_display", read_only=True)
    ecart = serializers.IntegerField(read_only=True)
    pourcentage_atteinte = serializers.FloatField(read_only=True)
    objectif_auto = serializers.IntegerField(source="get_objectif_auto", read_only=True)

    class Meta:
        model = SuiviJury
        fields = [
            "id", "centre_id", "centre_nom", "annee", "mois", "mois_libelle", "periode",
            "objectif_jury", "jurys_realises", "pourcentage_atteinte", "objectif_auto", "ecart",
            "created_at", "updated_at", "created_by", "updated_by", "is_active"
        ]
        read_only_fields = [
            "id", "centre_nom", "mois_libelle", "periode", "ecart",
            "pourcentage_atteinte", "objectif_auto",
            "created_at", "updated_at", "created_by", "updated_by", "is_active"
        ]
        extra_kwargs = {
            "annee": {"help_text": "Année concernée par le suivi (ex: 2024)"},
            "mois": {"help_text": "Mois concerné (1 = janvier, 12 = décembre)"},
            "objectif_jury": {"help_text": "Nombre de jurys prévus pour ce mois"},
            "jurys_realises": {"help_text": "Nombre de jurys effectivement réalisés"}
        }

    def validate_mois(self, value):
        if not (1 <= value <= 12):
            raise serializers.ValidationError("Le mois doit être compris entre 1 et 12.")
        return value


# -------------------- VAE --------------------

@extend_schema_serializer(examples=[
    OpenApiExample(
        name="Exemple VAE",
        value={
            "centre_id": 1,
            "statut": "accompagnement",
            "commentaire": "En phase d'accompagnement"
        }
    )
])
class VAESerializer(serializers.ModelSerializer):
    centre_nom = serializers.CharField(source="centre.nom", read_only=True)
    statut_libelle = serializers.CharField(source="get_statut_display", read_only=True)
    is_en_cours = serializers.BooleanField(read_only=True)
    is_terminee = serializers.BooleanField(read_only=True)
    duree_jours = serializers.IntegerField(read_only=True)
    duree_statut_actuel = serializers.IntegerField(read_only=True)

    class Meta:
        model = VAE
        fields = [
            "id", "reference", "centre_id", "centre_nom", "statut", "statut_libelle",
            "commentaire", "created_at", "updated_at", "created_by", "updated_by",
            "is_active", "is_en_cours", "is_terminee", "duree_jours", "duree_statut_actuel"
        ]
        read_only_fields = [
            "id", "reference", "centre_nom", "statut_libelle",
            "created_at", "updated_at", "created_by", "updated_by",
            "is_active", "is_en_cours", "is_terminee", "duree_jours", "duree_statut_actuel"
        ]
        extra_kwargs = {
            "statut": {"help_text": "Statut actuel de la VAE", "required": False},
            "centre_id": {"help_text": "Centre auquel la VAE est rattachée"},
            "commentaire": {"help_text": "Remarques ou informations complémentaires", "required": False, "allow_blank": True},
        }

    def validate(self, data):
        """
        ✅ Définit un statut par défaut si non fourni
        """
        data.setdefault("statut", "info")
        return data


# -------------------- Changer Statut VAE --------------------

@extend_schema_serializer(examples=[
    OpenApiExample(
        name="Changement de statut VAE",
        value={
            "statut": "jury",
            "date_changement_effectif": "2024-04-01",
            "commentaire": "Prévu pour jury"
        }
    )
])
class ChangerStatutVAESerializer(serializers.Serializer):
    statut = serializers.ChoiceField(
        choices=VAE.STATUT_CHOICES,
        help_text="Nouveau statut à affecter à la VAE"
    )
    date_changement_effectif = serializers.DateField(
        required=False,
        help_text="Date effective du changement (par défaut: aujourd’hui)"
    )
    commentaire = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Commentaire associé au changement de statut"
    )

    def validate_statut(self, value):
        if value not in dict(VAE.STATUT_CHOICES):
            raise serializers.ValidationError("Statut non reconnu.")
        return value


# -------------------- Historique Statut VAE --------------------

@extend_schema_serializer(examples=[
    OpenApiExample(
        name="Exemple Historique Statut",
        value={
            "vae_id": 5,
            "statut": "accompagnement",
            "date_changement_effectif": "2024-04-01",
            "commentaire": "Entrée en accompagnement"
        }
    )
])
class HistoriqueStatutVAESerializer(serializers.ModelSerializer):
    vae_reference = serializers.CharField(source="vae.reference", read_only=True)
    statut_libelle = serializers.CharField(source="get_statut_display", read_only=True)

    class Meta:
        model = HistoriqueStatutVAE
        fields = [
            "id", "vae_id", "vae_reference", "statut", "statut_libelle",
            "date_changement_effectif", "commentaire",
            "created_at", "created_by"
        ]
        read_only_fields = [
            "id", "vae_reference", "statut_libelle", "created_at", "created_by"
        ]
