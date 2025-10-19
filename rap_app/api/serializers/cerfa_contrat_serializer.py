from rest_framework import serializers
from django.core.exceptions import ValidationError
from ...models.cerfa_contrats import CerfaRemuneration
from ...models import CerfaContrat


# ─────────────────────────────────────────────
# 🔹 Serializer Rémunération
# ─────────────────────────────────────────────
class CerfaRemunerationSerializer(serializers.ModelSerializer):
    """Détail d’une période de rémunération liée à un CerfaContrat."""

    class Meta:
        model = CerfaRemuneration
        fields = [
            "id",
            "annee",
            "date_debut",
            "date_fin",
            "pourcentage",
            "reference",
            "montant_mensuel_estime",
        ]
        read_only_fields = ["id"]


# ─────────────────────────────────────────────
# 🔹 Serializer principal : CERFA CONTRAT
# ─────────────────────────────────────────────
class CerfaContratSerializer(serializers.ModelSerializer):
    """Serializer principal du CERFA Contrat d’apprentissage."""

    remunerations = CerfaRemunerationSerializer(many=True, required=False)
    pdf_url = serializers.SerializerMethodField()
    pdf_status = serializers.SerializerMethodField()
    missing_fields = serializers.SerializerMethodField()

    # Relations ForeignKey (lecture seule)
    candidat_nom = serializers.CharField(source="candidat.nom", read_only=True)
    formation_nom = serializers.CharField(source="formation.nom", read_only=True)
    employeur_nom_partenaire = serializers.CharField(source="employeur.nom", read_only=True)

    class Meta:
        model = CerfaContrat
        fields = "__all__"
        read_only_fields = [
            "id",
            "pdf_fichier",
            "created_at",
            "updated_at",
        ]

    # ───────────── Champs calculés ─────────────
    def get_pdf_url(self, obj):
        request = self.context.get("request")
        try:
            if obj.pdf_fichier and hasattr(obj.pdf_fichier, "url") and request:
                return request.build_absolute_uri(obj.pdf_fichier.url)
        except Exception:
            pass
        return None

    def get_pdf_status(self, obj):
        if not obj.pdf_fichier:
            return "missing"
        try:
            if obj.pdf_fichier.storage.exists(obj.pdf_fichier.name):
                return "ready"
        except Exception:
            pass
        return "missing"

    # ───────────── Détection des champs manquants ─────────────
    def _collect_missing_fields(self, cerfa: CerfaContrat):
        """Collecte les champs essentiels manquants sans bloquer la sauvegarde."""
        missing = []

        # 🔹 Employeur
        if not cerfa.employeur:
            missing.append("Employeur/partenaire manquant")
        elif not getattr(cerfa.employeur, "siret", None):
            missing.append("SIRET de l’employeur")

        # 🔹 Apprenti
        if not cerfa.apprenti_nom_naissance:
            missing.append("Nom de l’apprenti")
        if not cerfa.apprenti_prenom:
            missing.append("Prénom de l’apprenti")
        if not cerfa.apprenti_date_naissance:
            missing.append("Date de naissance de l’apprenti")

        # 🔹 Formation
        if not cerfa.formation:
            missing.append("Formation non renseignée")
        if not cerfa.diplome_vise:
            missing.append("Diplôme visé manquant")

        return missing

    def get_missing_fields(self, obj):
        try:
            return self._collect_missing_fields(obj)
        except Exception:
            return []

    # ───────────── Création avec auto-remplissage ─────────────
    def create(self, validated_data):
        remunerations_data = validated_data.pop("remunerations", [])

        cerfa = CerfaContrat(**validated_data)

        try:
            cerfa.populate_auto()
        except ValidationError:
            # on ignore les erreurs de validation internes (non bloquant)
            pass

        cerfa.save()

        for remun_data in remunerations_data:
            CerfaRemuneration.objects.create(contrat=cerfa, **remun_data)

        return cerfa  # ✅ DRF attend l’instance, pas un dict

    # ───────────── Mise à jour complète ─────────────
    def update(self, instance, validated_data):
        remunerations_data = validated_data.pop("remunerations", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        try:
            instance.populate_auto()
        except ValidationError:
            pass

        instance.save()

        if remunerations_data is not None:
            instance.remunerations.all().delete()
            for remun_data in remunerations_data:
                CerfaRemuneration.objects.create(contrat=instance, **remun_data)

        return instance  # ✅ idem  
 