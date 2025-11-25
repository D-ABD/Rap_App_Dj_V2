from rest_framework import serializers
from ...models.cvtheque import CVTheque
from ...models.candidat import Candidat


# ----------------------------------------------------------
# 🔹 MINI — Candidat
# ----------------------------------------------------------
class CandidatMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidat
        fields = [
            "id",
            "nom",
            "prenom",
            "email",
            "telephone",
            "ville",
            "code_postal",
            "formation",
            "statut",
            "cv_statut",
        ]


# ----------------------------------------------------------
# 🔹 BASE MIXIN — LIST + DETAIL
# ----------------------------------------------------------
class CVThequeBaseSerializer(serializers.ModelSerializer):
    candidat = CandidatMiniSerializer(read_only=True)

    extension = serializers.CharField(read_only=True)
    taille = serializers.CharField(read_only=True)

    # 🔐 URLs sécurisées
    download_url = serializers.SerializerMethodField()
    preview_url = serializers.SerializerMethodField()

    # Champs formation
    formation_nom = serializers.SerializerMethodField()
    formation_centre = serializers.SerializerMethodField()
    formation_type_offre = serializers.SerializerMethodField()
    formation_num_offre = serializers.SerializerMethodField()

    # -------------------------------
    # API Download URL
    # -------------------------------
    def get_download_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(f"/api/cvtheque/{obj.id}/download/")

    # -------------------------------
    # API Preview URL
    # -------------------------------
    def get_preview_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(f"/api/cvtheque/{obj.id}/preview/")

    # -------------------------------
    # Infos formation
    # -------------------------------
    def get_formation_nom(self, obj):
        f = getattr(obj.candidat, "formation", None)
        return getattr(f, "nom", None)

    def get_formation_centre(self, obj):
        f = getattr(obj.candidat, "formation", None)
        c = getattr(f, "centre", None)
        return getattr(c, "nom", None)

    def get_formation_type_offre(self, obj):
        f = getattr(obj.candidat, "formation", None)
        t = getattr(f, "type_offre", None)
        return getattr(t, "nom", None)

    def get_formation_num_offre(self, obj):
        f = getattr(obj.candidat, "formation", None)
        return getattr(f, "num_offre", None)


# ----------------------------------------------------------
# 🔹 LIST SERIALIZER
# ----------------------------------------------------------
class CVThequeListSerializer(CVThequeBaseSerializer):
    class Meta:
        model = CVTheque
        fields = [
            "id",
            "titre",
            "document_type",
            "date_depot",
            "est_public",
            "extension",
            "taille",
            "preview_url",     # preview sécurisé
            "download_url",    # download sécurisé
            "candidat",

            # Formation
            "formation_nom",
            "formation_centre",
            "formation_type_offre",
            "formation_num_offre",
        ]


# ----------------------------------------------------------
# 🔹 DETAIL SERIALIZER
# ----------------------------------------------------------
class CVThequeDetailSerializer(CVThequeBaseSerializer):
    formation_statut = serializers.SerializerMethodField()
    formation_start_date = serializers.SerializerMethodField()
    formation_end_date = serializers.SerializerMethodField()
    formation_resume = serializers.SerializerMethodField()

    class Meta:
        model = CVTheque
        fields = [
            "id",
            "document_type",
            "titre",
            "mots_cles",
            "est_public",
            "date_depot",
            "extension",
            "taille",
            "preview_url",     # preview sécurisé
            "download_url",    # download sécurisé
            "candidat",

            # Formation enrichie
            "formation_nom",
            "formation_num_offre",
            "formation_type_offre",
            "formation_statut",
            "formation_centre",
            "formation_start_date",
            "formation_end_date",
            "formation_resume",
        ]

    # ===== Helpers formation =====
    def _formation(self, obj):
        return getattr(obj.candidat, "formation", None)

    def get_formation_statut(self, obj):
        f = self._formation(obj)
        return getattr(f.statut, "nom", None) if f and f.statut else None

    def get_formation_start_date(self, obj):
        f = self._formation(obj)
        return getattr(f, "start_date", None)

    def get_formation_end_date(self, obj):
        f = self._formation(obj)
        return getattr(f, "end_date", None)

    def get_formation_resume(self, obj):
        f = self._formation(obj)
        return getattr(f, "resume", None)


# ----------------------------------------------------------
# 🔹 WRITE SERIALIZER
# ----------------------------------------------------------
class CVThequeWriteSerializer(serializers.ModelSerializer):
    candidat = serializers.PrimaryKeyRelatedField(
        queryset=Candidat.objects.all(),
        required=False,
        allow_null=True
    )
    fichier = serializers.FileField(required=False)

    class Meta:
        model = CVTheque
        fields = [
            "id",
            "candidat",
            "document_type",
            "titre",
            "mots_cles",
            "est_public",
            "fichier",
        ]

    def validate_titre(self, value):
        if not value.strip():
            raise serializers.ValidationError("Le titre est obligatoire.")
        return value

    def validate(self, attrs):
        fichier = attrs.get("fichier")
        if fichier and fichier.size > 5 * 1024 * 1024:
            raise serializers.ValidationError({"fichier": "Le fichier ne doit pas dépasser 5 Mo."})
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user if request and request.user.is_authenticated else None

        validated_data["created_by"] = user
        validated_data["updated_by"] = user

        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get("request")
        user = request.user if request and request.user.is_authenticated else None

        validated_data["updated_by"] = user

        # Si aucun fichier envoyé → ne pas remplacer l'ancien
        if "fichier" not in validated_data:
            validated_data.pop("fichier", None)

        return super().update(instance, validated_data)
