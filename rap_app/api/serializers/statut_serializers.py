from rest_framework import serializers
import re
from ...models.statut import Statut


class StatutSerializer(serializers.ModelSerializer):
    libelle = serializers.SerializerMethodField(
        help_text="Libellé affiché du statut (remplace 'Autre' par description personnalisée)."
    )
    badge_html = serializers.SerializerMethodField(
        help_text="Code HTML d’un badge coloré pour affichage visuel dans l’interface."
    )

    id = serializers.IntegerField(read_only=True, help_text="ID unique du statut.")
    nom = serializers.ChoiceField(
        choices=Statut.STATUT_CHOICES,
        help_text="Nom interne du statut (choix prédéfini)."
    )
    couleur = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Code couleur hexadécimal du statut (#RRGGBB)."
    )
    description_autre = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Description personnalisée pour les statuts de type 'Autre'."
    )

    created_at = serializers.DateTimeField(read_only=True, help_text="Date de création.")
    updated_at = serializers.DateTimeField(read_only=True, help_text="Date de dernière modification.")
    created_by = serializers.SerializerMethodField(help_text="Utilisateur ayant créé ce statut.")
    updated_by = serializers.SerializerMethodField(help_text="Dernier utilisateur ayant modifié ce statut.")
    is_active = serializers.BooleanField(read_only=True, help_text="Indique si le statut est actif ou supprimé logiquement.")

    class Meta:
        model = Statut
        fields = [
            "id", "nom", "couleur", "description_autre",
            "libelle", "badge_html",
            "created_at", "updated_at", "created_by", "updated_by", "is_active"
        ]

    def get_libelle(self, obj):
        return obj.get_nom_display()

    def get_badge_html(self, obj):
        return obj.get_badge_html()

    def get_created_by(self, obj):
        return getattr(obj.created_by, 'username', None)

    def get_updated_by(self, obj):
        return getattr(obj.updated_by, 'username', None)

    def validate(self, data):
        nom = data.get("nom")
        couleur = data.get("couleur")
        description_autre = data.get("description_autre")

        if nom == Statut.AUTRE and not description_autre:
            raise serializers.ValidationError({
                "description_autre": "Le champ 'description personnalisée' est requis pour le statut 'Autre'."
            })

        if couleur and not re.match(r'^#[0-9A-Fa-f]{6}$', couleur):
            raise serializers.ValidationError({
                "couleur": "La couleur doit être au format hexadécimal valide (#RRGGBB)."
            })

        return data
