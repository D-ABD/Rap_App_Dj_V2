# rap_app/api/serializers/centre_serializers.py

from rest_framework import serializers
from ...models.centres import Centre
from drf_spectacular.utils import extend_schema_field


class CentreSerializer(serializers.ModelSerializer):
    """
    Sérialiseur complet du modèle Centre.
    Expose tous les champs déclarés dans le modèle, y compris les champs calculés.
    """

    full_address = serializers.CharField(read_only=True, help_text="Adresse complète du centre.")
    nb_prepa_comp_global = serializers.SerializerMethodField(help_text="Nombre de PrepaCompGlobal associés.")

    class Meta:
        model = Centre
        fields = [
            # Champs système / métadonnées
            "id",
            "created_at",
            "updated_at",
            "is_active",

            # Champs principaux
            "nom",
            "numero_voie",
            "nom_voie",
            "complement_adresse",
            "code_postal",
            "commune",
            "numero_uai_centre",
            "siret_centre",

            # CFA d’entreprise
            "cfa_entreprise",

            # CFA Responsable
            "cfa_responsable_est_lieu_principal",
            "cfa_responsable_denomination",
            "cfa_responsable_uai",
            "cfa_responsable_siret",
            "cfa_responsable_numero",
            "cfa_responsable_voie",
            "cfa_responsable_complement",
            "cfa_responsable_code_postal",
            "cfa_responsable_commune",

            # Champs calculés
            "full_address",
            "nb_prepa_comp_global",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "full_address",
            "nb_prepa_comp_global",
        ]

    @extend_schema_field(serializers.IntegerField())
    def get_nb_prepa_comp_global(self, obj):
        return obj.nb_prepa_comp_global


class CentreConstantsSerializer(serializers.Serializer):
    """
    Sérialiseur exposant les constantes du modèle Centre.
    """
    nom_max_length = serializers.IntegerField(default=Centre.NOM_MAX_LENGTH)
    code_postal_length = serializers.IntegerField(default=Centre.CODE_POSTAL_LENGTH)
