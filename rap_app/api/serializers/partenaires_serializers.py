# serializers/partenaire_serializers.py

from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from django.utils.translation import gettext_lazy as _
from ...models.partenaires import Partenaire

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name="Partenaire exemple",
            value={
                "nom": "ACME Corp",
                "type": "entreprise",
                "secteur_activite": "Informatique",
                "contact_nom": "Jean Dupont",
                "contact_email": "jean.dupont@acme.fr",
                "contact_telephone": "0601020303",
                "city": "Paris",
                "zip_code": "75001",
                "website": "https://acme.fr",
            },
            response_only=False,
        )
    ]
)
class PartenaireSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source="get_type_display", read_only=True)
    actions_display = serializers.CharField(source="get_actions_display", read_only=True)

    # 👇 Fix pour éviter l'enum avec une valeur vide
    actions = serializers.ChoiceField(
        choices=Partenaire.CHOICES_TYPE_OF_ACTION,
        required=False,
        allow_blank=False,  # ⛔️ interdit ""
    )

    class Meta:
        model = Partenaire
        fields = [
            "id", "nom", "type", "type_display", "secteur_activite",
            "street_name", "zip_code", "city", "country",
            "contact_nom", "contact_poste", "contact_telephone", "contact_email",
            "website", "social_network_url",
            "actions", "actions_display", "action_description",
            "description", "slug",
            "created_at", "updated_at", "is_active"
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at", "type_display", "actions_display"]

        extra_kwargs = {
            "nom": {
                "required": True,
                "error_messages": {
                    "required": _("Création échouée : le champ 'nom' est requis."),
                    "blank": _("Le champ 'nom' ne peut pas être vide."),
                },
                "help_text": "Nom unique de l'entité partenaire",
            },
            "type": {
                "help_text": "Type de partenaire (entreprise, institutionnel, personne)",
            },
            "secteur_activite": {
                "help_text": "Secteur d'activité principal",
            },
            "zip_code": {
                "help_text": "Code postal (5 chiffres)",
            },
            "city": {
                "help_text": "Ville",
            },
            "contact_nom": {
                "help_text": "Nom complet du contact",
            },
            "contact_email": {
                "help_text": "Adresse email du contact",
            },
            "contact_telephone": {
                "help_text": "Numéro de téléphone au format français",
            },
            "website": {
                "help_text": "URL du site web (doit commencer par http:// ou https://)",
            },
            "social_network_url": {
                "help_text": "URL d’un réseau social (LinkedIn, etc.)",
            },
            "actions": {
                "help_text": "Catégorie d'action (partenariat, coaching, etc.)",
            },
            "action_description": {
                "help_text": "Détails sur les actions menées",
            },
            "description": {
                "help_text": "Description libre du partenaire",
            },
        }

    def to_representation(self, instance):
        return {
            "success": True,
            "message": "Partenaire récupéré avec succès.",
            "data": instance.to_serializable_dict(include_relations=True)
        }

    def create(self, validated_data):
        partenaire = Partenaire.objects.create(**validated_data)
        return partenaire

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return {
            "success": True,
            "message": "Partenaire mis à jour avec succès.",
            "data": instance.to_serializable_dict(include_relations=True)
        }

class PartenaireChoiceSerializer(serializers.Serializer):
    value = serializers.CharField(help_text="Valeur interne (ex: 'entreprise')")
    label = serializers.CharField(help_text="Libellé lisible (ex: 'Entreprise')")


class PartenaireChoicesResponseSerializer(serializers.Serializer):
    types = PartenaireChoiceSerializer(many=True)
    actions = PartenaireChoiceSerializer(many=True)
