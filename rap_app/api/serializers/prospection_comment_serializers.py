from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
import bleach

from ...models.prospection_comments import ProspectionComment
from ...models.prospection import Prospection


class ProspectionCommentSerializer(serializers.ModelSerializer):
    # Entrée : le front envoie prospection_id
    prospection_id = serializers.PrimaryKeyRelatedField(
        source="prospection",
        queryset=Prospection.objects.all(),
        write_only=True,
    )
    # Sortie : exposer l'id simple (pas d'objet)
    prospection = serializers.IntegerField(source="prospection_id", read_only=True)

    # ✅ Champs calculés
    est_archive = serializers.SerializerMethodField(read_only=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)

    partenaire_nom = serializers.SerializerMethodField(read_only=True)
    formation_nom = serializers.SerializerMethodField(read_only=True)
    prospection_text = serializers.SerializerMethodField(read_only=True)

    # ✅ Nouveaux champs
    prospection_owner = serializers.IntegerField(source="prospection.owner_id", read_only=True)
    prospection_owner_username = serializers.CharField(source="prospection.owner.username", read_only=True)
    prospection_partenaire = serializers.IntegerField(source="prospection.partenaire_id", read_only=True)

    statut_commentaire_display = serializers.CharField(
        source="get_statut_commentaire_display", read_only=True
    )

    class Meta:
        model = ProspectionComment
        fields = [
            "id",
            "prospection_id",
            "prospection",
            "prospection_owner",
            "prospection_owner_username",
            "prospection_partenaire",
            "partenaire_nom",
            "formation_nom",
            "prospection_text",
            "body",
            "is_internal",
            "statut_commentaire",
            "statut_commentaire_display",
            "est_archive",
            "created_by_username",
            "created_at",
            "updated_at",  # ✅ nouvelle inclusion
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "created_by_username",
            "prospection",
            "prospection_owner",
            "prospection_owner_username",
            "prospection_partenaire",
            "partenaire_nom",
            "formation_nom",
            "prospection_text",
            "statut_commentaire_display",
            "est_archive",
        ]

    # === Méthodes calculées ===
    def get_est_archive(self, obj: ProspectionComment) -> bool:
        return obj.est_archive

    def _safe_label(self, obj, candidates):
        for name in candidates:
            if hasattr(obj, name):
                val = getattr(obj, name)
                if isinstance(val, str) and val.strip():
                    return val
        return None

    def get_partenaire_nom(self, obj: ProspectionComment):
        partenaire = getattr(obj.prospection, "partenaire", None)
        if not partenaire:
            return None
        return self._safe_label(partenaire, ["nom", "name", "libelle", "label", "titre", "intitule"])

    def get_formation_nom(self, obj: ProspectionComment):
        formation = getattr(obj.prospection, "formation", None)
        if not formation:
            return None
        return self._safe_label(formation, ["nom", "intitule", "titre", "name", "libelle", "label"])

    def get_prospection_text(self, obj: ProspectionComment) -> str:
        partner = self.get_partenaire_nom(obj)
        formation = self.get_formation_nom(obj)
        parts = [p for p in (partner, formation) if p]
        return " • ".join(parts) if parts else f"#{obj.prospection_id}"

    # === Validation ===
    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        prospection = attrs.get("prospection") or getattr(self.instance, "prospection", None)
        is_internal = attrs.get("is_internal", getattr(self.instance, "is_internal", False))
        statut_commentaire = attrs.get(
            "statut_commentaire", getattr(self.instance, "statut_commentaire", "actif")
        )

        if not user or not user.is_authenticated:
            raise serializers.ValidationError(_("Authentification requise."))

        if hasattr(user, "is_candidat_or_stagiaire") and user.is_candidat_or_stagiaire():
            if prospection is None or prospection.owner_id != user.id:
                raise serializers.ValidationError(_("Vous ne pouvez commenter que vos propres prospections."))
            if is_internal:
                raise serializers.ValidationError(_("Un candidat ne peut pas créer un commentaire interne."))
            if statut_commentaire != "actif":
                raise serializers.ValidationError(_("Un candidat ne peut pas archiver un commentaire."))
            if self.instance is not None and "prospection" in attrs and prospection.id != self.instance.prospection_id:
                raise serializers.ValidationError(_("Vous ne pouvez pas changer la prospection d'un commentaire."))

        return attrs

    # === Validation & nettoyage du contenu HTML ===
    def validate_body(self, value: str) -> str:
        """Nettoie le HTML pour éviter le XSS tout en gardant la mise en forme simple."""
        allowed_tags = ["b", "i", "u", "strong", "em", "p", "br", "ul", "ol", "li", "a"]
        allowed_attrs = {"a": ["href", "title", "target"]}
        cleaned = bleach.clean(value or "", tags=allowed_tags, attributes=allowed_attrs, strip=True)
        return bleach.linkify(cleaned)

    # === Mise à jour ===
    def update(self, instance: ProspectionComment, validated_data):
        contenu = validated_data.get("body", instance.body)
        instance.body = self.validate_body(contenu)
        for attr, value in validated_data.items():
            if attr != "body":
                setattr(instance, attr, value)
        instance.save(update_fields=["body", "updated_at"])
        return instance
