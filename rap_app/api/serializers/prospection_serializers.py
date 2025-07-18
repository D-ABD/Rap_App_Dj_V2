from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, extend_schema_field, OpenApiExample
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ...models.prospection import Prospection, ProspectionChoices, HistoriqueProspection


class BaseProspectionSerializer(serializers.ModelSerializer):
    partenaire_nom = serializers.CharField(source="partenaire.nom", read_only=True)
    formation_nom = serializers.CharField(source="formation.nom", read_only=True)

    # Champs display
    statut_display = serializers.CharField(source="get_statut_display", read_only=True)
    objectif_display = serializers.CharField(source="get_objectif_display", read_only=True)
    motif_display = serializers.CharField(source="get_motif_display", read_only=True)
    type_prospection_display = serializers.CharField(source="get_type_prospection_display", read_only=True)

    # Champs calculés
    prochain_contact = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(read_only=True)
    relance_necessaire = serializers.BooleanField(read_only=True)

    created_by = serializers.StringRelatedField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    @extend_schema_field(serializers.DateTimeField(allow_null=True))
    def get_prochain_contact(self, obj) -> str | None:
        return obj.prochain_contact.isoformat() if obj.prochain_contact else None


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name="Exemple de prospection",
            value={
                "partenaire": 1,
                "formation": 2,
                "date_prospection": "2025-05-10T14:00:00",
                "type_prospection": "premier_contact",
                "motif": "partenariat",
                "statut": "en_cours",
                "objectif": "presentation_offre",
                "commentaire": "Entretien en cours"
            },
            response_only=False,
        )
    ]
)
class ProspectionSerializer(BaseProspectionSerializer):
    class Meta:
        model = Prospection
        fields = [
            "id", "partenaire", "partenaire_nom",
            "formation", "formation_nom",
            "date_prospection",
            "type_prospection", "type_prospection_display",
            "motif", "motif_display",
            "statut", "statut_display",
            "objectif", "objectif_display",
            "commentaire",
            "prochain_contact", "is_active", "relance_necessaire",
            "created_by", "created_at", "updated_at"
        ]
        read_only_fields = [
            "id", "created_at", "updated_at", "created_by",
            "partenaire_nom", "formation_nom",
            "statut_display", "objectif_display", 
            "type_prospection_display", "motif_display",
            "prochain_contact", "is_active", "relance_necessaire"
        ]
        extra_kwargs = {
            "partenaire": {"help_text": "ID du partenaire concerné"},
            "formation": {"help_text": "ID de la formation associée (optionnelle)"},
            "date_prospection": {"help_text": "Date et heure de la prospection"},
            "type_prospection": {"help_text": "Type de prospection (ex: premier_contact)"},
            "motif": {"help_text": "Motif de la prospection"},
            "statut": {"help_text": "Statut actuel de la prospection"},
            "objectif": {"help_text": "Objectif visé par la prospection"},
            "commentaire": {"help_text": "Commentaires ou observations"},
        }

    def validate(self, data):
        if data.get('statut') == ProspectionChoices.STATUT_ACCEPTEE and \
           data.get('objectif') != ProspectionChoices.OBJECTIF_CONTRAT:
            raise serializers.ValidationError(
                _("Une prospection acceptée doit avoir pour objectif un contrat.")
            )

        if data.get('statut') in [ProspectionChoices.STATUT_REFUSEE, ProspectionChoices.STATUT_ANNULEE] and \
           not data.get('commentaire'):
            raise serializers.ValidationError({
                "commentaire": _("Un commentaire est requis pour les statuts refusé ou annulé.")
            })

        return data

    def validate_date_prospection(self, value):
        if value > timezone.now():
            raise serializers.ValidationError("La date de prospection ne peut pas être dans le futur.")
        return value


class ChangerStatutSerializer(serializers.Serializer):
    statut = serializers.ChoiceField(choices=ProspectionChoices.PROSPECTION_STATUS_CHOICES)
    commentaire = serializers.CharField(required=False, allow_blank=True)
    moyen_contact = serializers.ChoiceField(choices=ProspectionChoices.MOYEN_CONTACT_CHOICES, required=False)
    prochain_contact = serializers.DateField(required=False)

    def validate(self, data):
        if data['statut'] == ProspectionChoices.STATUT_A_RELANCER and not data.get('prochain_contact'):
            data['prochain_contact'] = timezone.now().date() + timezone.timedelta(days=7)
        return data


class ProspectionListSerializer(BaseProspectionSerializer):
    class Meta:
        model = Prospection
        fields = [
            "id", "partenaire_nom", "formation_nom",
            "date_prospection",
            "type_prospection", "type_prospection_display",
            "statut", "statut_display",
            "objectif", "objectif_display",
            "prochain_contact", "relance_necessaire",
        ]



class ProspectionDetailSerializer(BaseProspectionSerializer):
    class Meta:
        model = Prospection
        fields = [
            "id", "partenaire", "partenaire_nom",
            "formation", "formation_nom",
            "date_prospection",
            "type_prospection", "type_prospection_display",
            "motif", "motif_display",
            "statut", "statut_display",
            "objectif", "objectif_display",
            "commentaire",
            "prochain_contact", "is_active", "relance_necessaire",
            "created_by", "created_at", "updated_at"
        ]
        read_only_fields = fields  # tout en lecture seule ici

class HistoriqueProspectionSerializer(serializers.ModelSerializer):
    type_prospection_display = serializers.CharField(source="get_type_prospection_display", read_only=True)
    ancien_statut_display = serializers.CharField(source="get_ancien_statut_display", read_only=True)
    nouveau_statut_display = serializers.CharField(source="get_nouveau_statut_display", read_only=True)
    moyen_contact_display = serializers.CharField(source="get_moyen_contact_display", read_only=True)

    jours_avant_relance = serializers.IntegerField(read_only=True)
    relance_urgente = serializers.BooleanField(read_only=True)
    est_recent = serializers.BooleanField(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)

    statut_avec_icone = serializers.SerializerMethodField()

    type_prospection = serializers.ChoiceField(
        choices=ProspectionChoices.TYPE_PROSPECTION_CHOICES
    )
    ancien_statut = serializers.ChoiceField(
        choices=ProspectionChoices.PROSPECTION_STATUS_CHOICES
    )
    nouveau_statut = serializers.ChoiceField(
        choices=ProspectionChoices.PROSPECTION_STATUS_CHOICES
    )
    moyen_contact = serializers.ChoiceField(
        choices=ProspectionChoices.MOYEN_CONTACT_CHOICES,
        required=False
    )

    class Meta:
        model = HistoriqueProspection
        fields = [
            "id", "prospection",
            "date_modification",
            "ancien_statut", "ancien_statut_display",
            "nouveau_statut", "nouveau_statut_display",
            "type_prospection", "type_prospection_display",
            "commentaire", "resultat",
            "prochain_contact",
            "moyen_contact", "moyen_contact_display",
            "jours_avant_relance", "relance_urgente", "est_recent",
            "created_by", "statut_avec_icone"
        ]
        read_only_fields = [
            "id", "date_modification",
            "ancien_statut_display", "nouveau_statut_display",
            "type_prospection_display", "moyen_contact_display",
            "jours_avant_relance", "relance_urgente", "est_recent",
            "created_by", "statut_avec_icone"
        ]
        extra_kwargs = {
            "prospection": {"help_text": "ID de la prospection concernée"},
            "type_prospection": {"help_text": "Type de prospection (premier_contact, relance...)"},
            "ancien_statut": {"help_text": "Statut précédent"},
            "nouveau_statut": {"help_text": "Nouveau statut"},
            "commentaire": {"help_text": "Commentaire sur la modification"},
            "resultat": {"help_text": "Résultat obtenu"},
            "prochain_contact": {"help_text": "Date du prochain contact"},
            "moyen_contact": {"help_text": "Moyen de communication"},
        }

    def get_statut_avec_icone(self, obj) -> dict:
        return {
            "statut": obj.get_nouveau_statut_display(),
            "icone": "fas fa-check" if obj.nouveau_statut == ProspectionChoices.STATUT_ACCEPTEE else "fas fa-clock",
            "classe": "text-success" if obj.nouveau_statut == ProspectionChoices.STATUT_ACCEPTEE else "text-warning"
        }

    def validate_prochain_contact(self, value):
        if value and value < timezone.now().date():
            raise serializers.ValidationError(
                _("La date de relance doit être dans le futur.")
            )
        return value


class EnumChoiceSerializer(serializers.Serializer):
    value = serializers.CharField(help_text="Valeur brute utilisée en base")
    label = serializers.CharField(help_text="Libellé affiché (traduction)")


class ProspectionChoiceListSerializer(serializers.Serializer):
    statut = EnumChoiceSerializer(many=True)
    objectif = EnumChoiceSerializer(many=True)
    type_prospection = EnumChoiceSerializer(many=True)
    motif = EnumChoiceSerializer(many=True)
    moyen_contact = EnumChoiceSerializer(many=True)
