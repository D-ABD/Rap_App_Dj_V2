# rap_app/api/serializers/centre_serializers.py

from rest_framework import serializers
from ...models.centres import Centre


class CentreSerializer(serializers.ModelSerializer):
    """
    Sérialiseur du modèle Centre, basé sur to_serializable_dict.
    """
    full_address = serializers.CharField(read_only=True, help_text="Adresse complète du centre.")
    nb_prepa_comp_global = serializers.SerializerMethodField(help_text="Nombre de PrepaCompGlobal associés.")

    class Meta:
        model = Centre
        fields = [
            "id", "created_at", "updated_at", "is_active",
            "nom", "code_postal", "full_address", "nb_prepa_comp_global"
        ]
        read_only_fields = ["id", "created_at", "updated_at", "full_address", "nb_prepa_comp_global"]

    def get_nb_prepa_comp_global(self, obj):
        return obj.nb_prepa_comp_global