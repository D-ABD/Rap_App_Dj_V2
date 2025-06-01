# rap_app/api/serializers/centre_serializers.py

from rest_framework import serializers
from ...models.centres import Centre
from drf_spectacular.utils import extend_schema_field


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

    @extend_schema_field(serializers.IntegerField())
    def get_nb_prepa_comp_global(self, obj):
        return obj.nb_prepa_comp_global
    
class CentreConstantsSerializer(serializers.Serializer):
    nom_max_length = serializers.IntegerField(default=Centre.NOM_MAX_LENGTH)
    code_postal_length = serializers.IntegerField(default=Centre.CODE_POSTAL_LENGTH)
