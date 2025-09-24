from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from django.utils.translation import gettext_lazy as _

from ...models.commentaires_appairage import CommentaireAppairage


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name="Commentaire appairage (création)",
            value={
                "appairage": 12,
                "body": "Premier échange avec le partenaire.",
            },
            request_only=True,
        ),
        OpenApiExample(
            name="Réponse succès",
            value={
                "id": 42,
                "appairage": 12,
                "appairage_label": "Durand Jean → Formation Y",
                "body": "Premier échange avec le partenaire.",
                "auteur_nom": "Jean Dupont",
                "created_by_username": "jean.dupont",
                "candidat_nom": "Durand",
                "candidat_prenom": "Jean",
                "partenaire_nom": "Entreprise X",
                "formation_nom": "Formation Y",
                "formation_numero_offre": "FO-2025-001",
                "formation_centre": "Centre A",
                "formation_type_offre": "Collective",
                "statut_snapshot": "transmis",
                "appairage_statut_display": "Transmis",
                "created_at": "2025-09-13T11:20:00Z",
                "updated_at": "2025-09-13T11:20:00Z",
            },
            response_only=True,
        ),
    ]
)
class CommentaireAppairageSerializer(serializers.ModelSerializer):
    """
    🎯 Serializer lecture seule pour les commentaires d’appairage :
    - infos de base (id, body, auteur, dates)
    - infos enrichies sur l’appairage (candidat, partenaire, formation, statut…)
    """

    auteur_nom = serializers.SerializerMethodField()
    created_by_username = serializers.SerializerMethodField()

    candidat_nom = serializers.CharField(source="appairage.candidat.nom", read_only=True)
    candidat_prenom = serializers.CharField(source="appairage.candidat.prenom", read_only=True)
    partenaire_nom = serializers.CharField(source="appairage.partenaire.nom", read_only=True)

    formation_nom = serializers.CharField(source="appairage.formation.nom", read_only=True)
    formation_numero_offre = serializers.CharField(source="appairage.formation.numero_offre", read_only=True)
    formation_centre = serializers.CharField(source="appairage.formation.centre.nom", read_only=True)
    formation_type_offre = serializers.CharField(source="appairage.formation.type_offre.nom", read_only=True)

    appairage_label = serializers.SerializerMethodField()
    appairage_statut_display = serializers.CharField(source="appairage.get_statut_display", read_only=True)

    # ─────────── Helpers ───────────
    def get_auteur_nom(self, obj):
        u = getattr(obj, "created_by", None)
        if not u:
            return "Anonyme"
        return u.get_full_name() or getattr(u, "username", None) or getattr(u, "email", None)

    def get_created_by_username(self, obj):
        return getattr(getattr(obj, "created_by", None), "username", "—")

    def get_appairage_label(self, obj):
        cand = getattr(obj.appairage, "candidat", None)
        form = getattr(obj.appairage, "formation", None)
        if cand and form:
            return f"{cand.prenom} {cand.nom} → {form.nom}"
        if cand:
            return f"{cand.prenom} {cand.nom}"
        if form:
            return f"Formation {form.nom}"
        return f"Appairage {obj.appairage_id}"

    class Meta:
        model = CommentaireAppairage
        fields = [
            "id",
            "appairage",
            "appairage_label",
            "body",
            "auteur_nom",
            "created_by_username",
            "created_at",
            "updated_at",
            "candidat_nom",
            "candidat_prenom",
            "partenaire_nom",
            "formation_nom",
            "formation_numero_offre",
            "formation_centre",
            "formation_type_offre",
            "statut_snapshot",
            "appairage_statut_display",
        ]
        read_only_fields = fields


class CommentaireAppairageWriteSerializer(serializers.ModelSerializer):
    """
    ✍️ Serializer écriture (création / mise à jour)
    """

    class Meta:
        model = CommentaireAppairage
        fields = ["appairage", "body"]
 