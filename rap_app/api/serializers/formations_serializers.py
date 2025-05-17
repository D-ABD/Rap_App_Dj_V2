# rap_app/api/serializers/formations_serializers.py

import logging
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from ...models.formations import Formation, HistoriqueFormation
from ...models.commentaires import Commentaire
from ...models.documents import Document
from ...models.evenements import Evenement

logger = logging.getLogger("application.api.formation")


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name="Exemple de formation complète",
            value={
                "id": 1,
                "nom": "Prépa CléA",
                "centre": {"id": 1, "nom": "Centre Paris"},
                "type_offre": {"id": 2, "nom": "POEC"},
                "statut": {"id": 3, "nom": "En cours"},
                "start_date": "2025-05-15",
                "end_date": "2025-06-30",
                "total_places": 20,
                "total_inscrits": 12,
                "places_disponibles": 8,
                "taux_saturation": 60.0,
                "taux_transformation": 75.0,
                "statut_color": "#00BFFF",
                "status_temporel": "future",
                "created_at": "2025-01-01T10:00",
                "updated_at": "2025-02-01T14:30"
            },
            response_only=True
        )
    ]
)
class FormationSerializer(serializers.Serializer):
    """
    🎓 Serializer principal pour les formations.

    Sérialise les données complètes d'une formation avec :
    - Validation métier
    - Champs relationnels (centre, type_offre, statut)
    - Données calculées via `to_serializable_dict()`
    """

    id = serializers.IntegerField(read_only=True)
    nom = serializers.CharField(required=True, help_text="Nom complet de la formation")
    centre_id = serializers.IntegerField(required=True, write_only=True, help_text="ID du centre")
    type_offre_id = serializers.IntegerField(required=True, write_only=True, help_text="ID du type d'offre")
    statut_id = serializers.IntegerField(required=True, write_only=True, help_text="ID du statut")

    start_date = serializers.DateField(required=False, allow_null=True, help_text="Date de début")
    end_date = serializers.DateField(required=False, allow_null=True, help_text="Date de fin")
    num_kairos = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text="Numéro Kairos")
    num_offre = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text="Numéro offre")
    num_produit = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text="Numéro produit")

    prevus_crif = serializers.IntegerField(required=False, default=0, help_text="Places prévues CRIF")
    prevus_mp = serializers.IntegerField(required=False, default=0, help_text="Places prévues MP")
    inscrits_crif = serializers.IntegerField(required=False, default=0, help_text="Inscrits CRIF")
    inscrits_mp = serializers.IntegerField(required=False, default=0, help_text="Inscrits MP")
    assistante = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text="Assistante")
    cap = serializers.IntegerField(required=False, allow_null=True, help_text="Capacité maximale")
    convocation_envoie = serializers.BooleanField(default=False, help_text="Convocation envoyée")
    entree_formation = serializers.IntegerField(required=False, default=0, help_text="Entrées en formation")
    nombre_candidats = serializers.IntegerField(required=False, default=0, help_text="Candidats")
    nombre_entretiens = serializers.IntegerField(required=False, default=0, help_text="Entretiens")
    nombre_evenements = serializers.IntegerField(required=False, default=0, help_text="Événements")
    dernier_commentaire = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text="Dernier commentaire")

    centre = serializers.SerializerMethodField(read_only=True)
    type_offre = serializers.SerializerMethodField(read_only=True)
    statut = serializers.SerializerMethodField(read_only=True)

    def get_centre(self, obj):
        return {"id": obj.centre.id, "nom": obj.centre.nom} if obj.centre else None

    def get_type_offre(self, obj):
        return {"id": obj.type_offre.id, "nom": str(obj.type_offre)} if obj.type_offre else None

    def get_statut(self, obj):
        return {"id": obj.statut.id, "nom": obj.statut.nom} if obj.statut else None

    def validate(self, data):
        start = data.get("start_date")
        end = data.get("end_date")
        if start and end and start > end:
            raise serializers.ValidationError({
                "start_date": _("La date de début doit être antérieure à la date de fin."),
                "end_date": _("La date de fin doit être postérieure à la date de début."),
            })
        return data

    def create(self, validated_data):
        user = self.context["request"].user
        instance = Formation(**validated_data)
        try:
            instance.save(user=user)
            logger.info(f"[API] Formation créée : {instance.nom} par {user}")
        except ValidationError as e:
            logger.error(f"[API] Erreur création formation : {e}")
            raise serializers.ValidationError(e.message_dict)
        return instance

    def update(self, instance, validated_data):
        user = self.context["request"].user
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        try:
            instance.save(user=user)
            logger.info(f"[API] Formation mise à jour : {instance.nom} par {user}")
        except ValidationError as e:
            logger.error(f"[API] Erreur MAJ formation : {e}")
            raise serializers.ValidationError(e.message_dict)
        return instance

    def to_representation(self, instance):
        return {
            "success": True,
            "message": "Formation récupérée avec succès.",
            "data": instance.to_serializable_dict()
        }

    class Meta:
        ref_name = "FormationSerializer"


class CommentaireSerializer(serializers.Serializer):
    """
    💬 Serializer pour les commentaires d'une formation.
    """
    id = serializers.IntegerField(read_only=True)
    contenu = serializers.CharField(help_text="Contenu du commentaire")
    saturation = serializers.IntegerField(required=False, allow_null=True, help_text="Niveau de saturation (0 à 100)")
    created_by = serializers.CharField(source="created_by.username", read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    def to_representation(self, instance):
        return instance.to_serializable_dict()


class DocumentSerializer(serializers.Serializer):
    """
    📄 Serializer pour les documents liés à une formation.
    """
    id = serializers.IntegerField(read_only=True)
    nom_fichier = serializers.CharField(help_text="Nom lisible du document")
    fichier = serializers.FileField(help_text="Fichier attaché")
    type_document = serializers.CharField(help_text="Type du document (PDF, Image...)")
    est_public = serializers.BooleanField(default=False, help_text="Document visible par le public ?")
    created_by = serializers.CharField(source="created_by.username", read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    def to_representation(self, instance):
        return instance.to_serializable_dict()


class EvenementSerializer(serializers.Serializer):
    """
    📆 Serializer pour les événements d'une formation.
    """
    id = serializers.IntegerField(read_only=True)
    type_evenement = serializers.CharField(help_text="Type d'événement")
    event_date = serializers.DateField(help_text="Date de l'événement")
    details = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text="Détails supplémentaires")
    description_autre = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text="Description (si type autre)")
    created_by = serializers.CharField(source="created_by.username", read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    def to_representation(self, instance):
        return instance.to_serializable_dict()


class HistoriqueFormationSerializer(serializers.Serializer):
    """
    🕓 Serializer pour l'historique des modifications d'une formation.
    """
    id = serializers.IntegerField(read_only=True)
    champ_modifie = serializers.CharField(help_text="Champ concerné")
    ancienne_valeur = serializers.CharField(allow_blank=True, allow_null=True)
    nouvelle_valeur = serializers.CharField(allow_blank=True, allow_null=True)
    commentaire = serializers.CharField(allow_blank=True, allow_null=True)
    action = serializers.CharField()
    created_by = serializers.CharField(source="created_by.username", read_only=True)
    created_at = serializers.DateTimeField()

    def to_representation(self, instance):
        return instance.to_serializable_dict()
