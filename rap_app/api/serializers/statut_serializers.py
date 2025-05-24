from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, extend_schema_field
import re
from ...models.statut import Statut


@extend_schema_serializer(
)
class StatutSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle Statut.

    - Le champ `libelle` affiche un nom lisible, en particulier pour le statut 'Autre'.
    - Le champ `badge_html` fournit une représentation visuelle colorée pour l'interface.
    """

    libelle = serializers.SerializerMethodField(
        help_text="Libellé affiché du statut (remplace 'Autre' par une description personnalisée si définie)."
    )
    badge_html = serializers.SerializerMethodField(
        help_text="Code HTML pour un badge coloré représentant le statut visuellement."
    )

    id = serializers.IntegerField(read_only=True, help_text="ID unique du statut.")
    nom = serializers.ChoiceField(
        choices=Statut.STATUT_CHOICES,
        help_text="Nom interne du statut (valeurs définies en base)."
    )
    couleur = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Couleur hexadécimale du badge (#RRGGBB)."
    )
    description_autre = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Texte personnalisé pour le statut 'Autre'."
    )

    created_at = serializers.DateTimeField(read_only=True, help_text="Date de création.")
    updated_at = serializers.DateTimeField(read_only=True, help_text="Dernière mise à jour.")
    created_by = serializers.SerializerMethodField(help_text="Nom de l'utilisateur ayant créé ce statut.")
    updated_by = serializers.SerializerMethodField(help_text="Nom de l'utilisateur ayant modifié ce statut.")
    is_active = serializers.BooleanField(read_only=True, help_text="Statut actif ou désactivé (suppression logique).")

    class Meta:
        model = Statut
        fields = [
            "id", "nom", "couleur", "description_autre",
            "libelle", "badge_html",
            "created_at", "updated_at", "created_by", "updated_by", "is_active"
        ]

    @extend_schema_field(serializers.CharField())
    def get_libelle(self, obj) -> str:
        """Retourne le libellé affiché, adapté pour le statut 'Autre'."""
        return obj.get_nom_display()

    @extend_schema_field(serializers.CharField())
    def get_badge_html(self, obj) -> str:
        """Renvoie un badge HTML stylisé représentant visuellement le statut."""
        return obj.get_badge_html()

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_created_by(self, obj) -> str | None:
        """Nom de l'utilisateur ayant créé ce statut."""
        return getattr(obj.created_by, 'username', None)

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_updated_by(self, obj) -> str | None:
        """Nom du dernier utilisateur ayant modifié ce statut."""
        return getattr(obj.updated_by, 'username', None)

    def validate(self, data):
        """
        Valide :
        - La présence de `description_autre` si le nom est 'autre'
        - Le format de la couleur (hexadécimal)
        """
        nom = data.get("nom")
        couleur = data.get("couleur")
        description_autre = data.get("description_autre")

        if nom == Statut.AUTRE and not description_autre:
            raise serializers.ValidationError({
                "description_autre": "Le champ est requis pour un statut 'Autre'."
            })

        if couleur and not re.match(r'^#[0-9A-Fa-f]{6}$', couleur):
            raise serializers.ValidationError({
                "couleur": "La couleur doit être au format hexadécimal (#RRGGBB)."
            })

        return data
