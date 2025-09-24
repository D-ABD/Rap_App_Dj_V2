from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

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
    created_by_username = serializers.StringRelatedField(source="created_by", read_only=True)

    # 🔹 Champs display calculés depuis les FK réelles
    partenaire_nom = serializers.SerializerMethodField(read_only=True)
    formation_nom = serializers.SerializerMethodField(read_only=True)
    prospection_text = serializers.SerializerMethodField(read_only=True)

    # ✅ Nouveaux champs : owner & partenaire de la prospection (ids + username)
    prospection_owner = serializers.IntegerField(source="prospection.owner_id", read_only=True)
    prospection_owner_username = serializers.StringRelatedField(source="prospection.owner", read_only=True)
    prospection_partenaire = serializers.IntegerField(source="prospection.partenaire_id", read_only=True)

    class Meta:
        model = ProspectionComment
        fields = [
            "id",
            "prospection_id",              # write-only
            "prospection",                 # read-only (id)
            # ✅ nouveaux read-only
            "prospection_owner",
            "prospection_owner_username",
            "prospection_partenaire",
            # displays existants
            "partenaire_nom",
            "formation_nom",
            "prospection_text",
            # contenu
            "body",
            "is_internal",
            "created_by_username",
            "created_at",
            "updated_at",
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
        ]

    # -- Helpers robustes (supportent différents schémas de champs) --
    def _safe_label(self, obj, candidates):
        # candidates: liste de noms d'attributs à tester
        for name in candidates:
            if hasattr(obj, name):
                val = getattr(obj, name)
                if isinstance(val, str) and val.strip():
                    return val
        return None

    def get_partenaire_nom(self, obj: ProspectionComment):
        # Essaie prospection.partenaire.nom / name / libelle / label
        partenaire = getattr(obj.prospection, "partenaire", None)
        if not partenaire:
            return None
        return self._safe_label(partenaire, ["nom", "name", "libelle", "label", "titre", "intitule"])

    def get_formation_nom(self, obj: ProspectionComment):
        # Essaie prospection.formation.nom / intitule / titre / name
        formation = getattr(obj.prospection, "formation", None)
        if not formation:
            return None
        return self._safe_label(formation, ["nom", "intitule", "titre", "name", "libelle", "label"])

    def get_prospection_text(self, obj: ProspectionComment) -> str:
        partner = self.get_partenaire_nom(obj)
        formation = self.get_formation_nom(obj)
        parts = [p for p in (partner, formation) if p]
        return " • ".join(parts) if parts else f"#{obj.prospection_id}"

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        prospection = attrs.get("prospection") or getattr(self.instance, "prospection", None)
        is_internal = attrs.get("is_internal", getattr(self.instance, "is_internal", False))

        if not user or not user.is_authenticated:
            raise serializers.ValidationError(_("Authentification requise."))

        # Candidat/Stagiaire : uniquement ses prospections + pas d'interne
        if hasattr(user, "is_candidat_or_stagiaire") and user.is_candidat_or_stagiaire():
            if prospection is None or prospection.owner_id != user.id:
                raise serializers.ValidationError(_("Vous ne pouvez commenter que vos propres prospections."))
            if is_internal:
                raise serializers.ValidationError(_("Un candidat ne peut pas créer un commentaire interne."))
            # blocage du changement de prospection à l'update
            if self.instance is not None and "prospection" in attrs and prospection.id != self.instance.prospection_id:
                raise serializers.ValidationError(_("Vous ne pouvez pas changer la prospection d'un commentaire."))

        return attrs
