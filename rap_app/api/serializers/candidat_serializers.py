from rest_framework import serializers, exceptions
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

from ..serializers.commentaires_appairage_serializers import CommentaireAppairageSerializer

from ...models.atelier_tre import AtelierTRE
from ...models.centres import Centre
from ...models.formations import Formation
from ...models.candidat import (
    Candidat,
    HistoriquePlacement,
    ResultatPlacementChoices,
    NIVEAU_CHOICES,
)
from ...models.appairage import Appairage  # ✅ pour type hints/queries


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────




def _normalize_nom_prenom(instance):
    user = getattr(instance, "compte_utilisateur", None)

    nom = (getattr(instance, "nom", "") or "").strip()
    prenom = (getattr(instance, "prenom", "") or "").strip()

    if not nom and user:
        nom = (getattr(user, "last_name", "") or "").strip()
    if not prenom and user:
        prenom = (getattr(user, "first_name", "") or "").strip()

    nom_complet = " ".join(x for x in [nom, prenom] if x) or (
        getattr(user, "email", None) or f"Candidat #{getattr(instance, 'pk', '—')}"
    )
    return nom, prenom, nom_complet


def _user_display(u):
    if not u:
        return None
    full = u.get_full_name()
    return full or getattr(u, "email", None) or getattr(u, "username", None)


def _ateliers_counts_for(obj) -> dict[str, int]:
    """
    Retourne un mapping compact par type d'atelier :
    { 'atelier1': 0, 'atelier2': 3, ..., 'atelier7': 1, 'autre': 0 }
    - Utilise d'abord les annotations (count_atelier_1, …, count_atelier_autre)
    - Fallback: recompte via la M2M si pas annoté/prefetch absent
    """
    out: dict[str, int] = {}
    for key, _label in AtelierTRE.TypeAtelier.choices:
        # nom d’annotation par défaut
        annot_name = f"count_{key}"
        # alias possible pour 'autre' si tu as ajouté count_atelier_autre côté queryset
        if key == "autre" and hasattr(obj, "count_atelier_autre"):
            annot_name = "count_atelier_autre"

        val = getattr(obj, annot_name, None)
        if val is None:
            # fallback via la relation M2M
            rel = getattr(obj, "ateliers_tre", None)
            if hasattr(rel, "all"):
                try:
                    val = sum(1 for a in rel.all() if getattr(a, "type_atelier", None) == key)
                except Exception:
                    val = 0
            else:
                val = 0

        # clé compactée attendue côté front: "atelier_1" -> "atelier1"
        k = key.replace("atelier_", "atelier")
        out[k] = int(val or 0)

    return out



# ─────────────────────────────────────────────────────────────────────────────
# Formation lite  (dates exposées de manière tolérante)
# ─────────────────────────────────────────────────────────────────────────────
class FormationLiteSerializer(serializers.ModelSerializer):
    centre = serializers.SerializerMethodField()
    type_offre = serializers.SerializerMethodField()
    date_debut = serializers.SerializerMethodField()
    date_fin = serializers.SerializerMethodField()

    class Meta:
        model = Formation
        fields = ("id", "nom", "num_offre", "centre", "type_offre", "date_debut", "date_fin")

    def get_centre(self, obj):
        c = getattr(obj, "centre", None)
        return {"id": c.id, "nom": c.nom} if c else None

    def get_type_offre(self, obj):
        to = getattr(obj, "type_offre", None)
        if not to:
            return None
        return {
            "id": to.id,
            "nom": getattr(to, "nom", None),
            "libelle": getattr(to, "libelle", None),
            "couleur": getattr(to, "couleur", None),
        }

    def _first_attr(self, obj, names):
        for name in names:
            if hasattr(obj, name):
                val = getattr(obj, name)
                if val not in (None, ""):
                    return val
        return None

    def get_date_debut(self, obj):
        # tolère plusieurs dénominations côté modèle/DB
        return self._first_attr(obj, ["date_debut", "date_rentree", "debut", "start_date", "startDate"])

    def get_date_fin(self, obj):
        return self._first_attr(obj, ["date_fin", "fin", "end_date", "endDate"])


# ─────────────────────────────────────────────────────────────────────────────
# Appairage lite  ✅ POUR AFFICHER LE DERNIER APPAIRAGE DANS CANDIDAT
# ─────────────────────────────────────────────────────────────────────────────
class AppairageLiteSerializer(serializers.ModelSerializer):
    partenaire_nom = serializers.CharField(source="partenaire.nom", read_only=True)
    created_by_nom = serializers.SerializerMethodField()
    statut_display = serializers.CharField(source="get_statut_display", read_only=True)

    commentaire = serializers.SerializerMethodField()       # compat
    last_commentaire = serializers.SerializerMethodField()  # explicite
    commentaires = CommentaireAppairageSerializer(many=True, read_only=True)

    class Meta:
        model = Appairage
        fields = [
            "id",
            "partenaire",
            "partenaire_nom",
            "date_appairage",
            "statut",
            "statut_display",
            "commentaire",        # champ legacy
            "last_commentaire",   # dernier commentaire
            "commentaires",       # liste complète
            "retour_partenaire",
            "date_retour",
            "created_at",
            "updated_at",
            "created_by_nom",
        ]
        read_only_fields = fields

    def get_commentaire(self, obj):
        dernier = obj.commentaires.order_by("-created_at").first()
        return dernier.body if dernier else None

    def get_last_commentaire(self, obj):
        dernier = obj.commentaires.order_by("-created_at").first()
        return dernier.body if dernier else None

    def get_created_by_nom(self, obj: "Appairage") -> str | None:
        return _user_display(getattr(obj, "created_by", None))

# ─────────────────────────────────────────────────────────────────────────────
# Candidat (détail)
# ─────────────────────────────────────────────────────────────────────────────
@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Exemple de candidat",
            value={
                "id": 1,
                "nom": "Dupont",
                "prenom": "Alice",
                "email": "alice.dupont@example.com",
                "telephone": "0612345678",
                "ville": "Paris",
                "statut": "accompagnement",
                "cv_statut": "en_cours",
                "formation": 3,
                "date_naissance": "2000-01-01",
                "admissible": True,
            },
        )
    ]
)
class CandidatSerializer(serializers.ModelSerializer):
    age = serializers.IntegerField(read_only=True)
    nom_complet = serializers.CharField(read_only=True)
    nb_appairages = serializers.IntegerField(source="nb_appairages_calc", read_only=True)
    nb_prospections = serializers.IntegerField(source="nb_prospections_calc", read_only=True)
    role_utilisateur = serializers.CharField(read_only=True)
    ateliers_resume = serializers.CharField(read_only=True)
    peut_modifier = serializers.SerializerMethodField()
    cv_statut_display = serializers.CharField(read_only=True)
    ateliers_counts = serializers.SerializerMethodField()
    centre_id = serializers.IntegerField(source="formation.centre_id", read_only=True)
    centre_nom = serializers.CharField(source="formation.centre.nom", read_only=True)

    # ✅ projections utiles UI
    formation_info = FormationLiteSerializer(source="formation", read_only=True)
    last_appairage = serializers.SerializerMethodField()  # ✅ dernier appairage complet (lite)

    # ✅ Libellés visibles même pour non-staff
    responsable_placement_nom = serializers.SerializerMethodField()
    entreprise_placement_nom = serializers.SerializerMethodField()
    entreprise_validee_nom = serializers.SerializerMethodField()
    vu_par_nom = serializers.SerializerMethodField()
    resultat_placement_display = serializers.SerializerMethodField()

    class Meta:
        model = Candidat
        fields = "__all__"
        read_only_fields = [
            "age",
            "nom_complet",
            "nb_appairages",
            "nb_prospections",
            "role_utilisateur",
            "ateliers_resume",
            "peut_modifier",
            "cv_statut_display",
            "formation_info",
            "centre_nom", 
            "centre_id",
            "last_appairage",
            # read-only exposés
            "responsable_placement_nom",
            "entreprise_placement_nom",
            "entreprise_validee_nom",
            "vu_par_nom",
            "resultat_placement_display",
            "ateliers_counts",
        ]

    # ------- label getters -------
    def get_centre_nom(self, obj):
        f = getattr(obj, "formation", None)
        c = getattr(f, "centre", None) if f else None
        return getattr(c, "nom", None)
    
    def get_ateliers_counts(self, obj):
            return _ateliers_counts_for(obj)

    def get_responsable_placement_nom(self, obj):
        return _user_display(getattr(obj, "responsable_placement", None))

    def get_entreprise_placement_nom(self, obj):
        p = getattr(obj, "entreprise_placement", None)
        return getattr(p, "nom", None) if p else None

    def get_entreprise_validee_nom(self, obj):
        p = getattr(obj, "entreprise_validee", None)
        return getattr(p, "nom", None) if p else None

    def get_vu_par_nom(self, obj):
        return _user_display(getattr(obj, "vu_par", None))

    def get_resultat_placement_display(self, obj):
        return obj.get_resultat_placement_display() if getattr(obj, "resultat_placement", None) else None

    def get_last_appairage(self, obj):
        last = (
            obj.appairages.order_by("-date_appairage", "-pk")
            .select_related("partenaire", "created_by")
            .first()
        )
        return AppairageLiteSerializer(last, context=self.context).data if last else None
    # -----------------------------

    def get_peut_modifier(self, instance):
        request = self.context.get("request")
        user = request.user if request and request.user.is_authenticated else None
        if not user:
            return False
        return user.role in ["admin", "superadmin", "staff"] or instance.compte_utilisateur == user

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # ❄️ Normalisation du nom/prenom/nom_complet
        nom, prenom, nom_complet = _normalize_nom_prenom(instance)
        data["nom"] = nom
        data["prenom"] = prenom
        data["nom_complet"] = nom_complet

        # 🔒 Masquage conditionnel (on laisse les *_nom et last_appairage visibles)
        request = self.context.get("request")
        user = request.user if request and request.user.is_authenticated else None
        role = getattr(user, "role", None)
        is_staff_or_admin = role in ["staff", "admin", "superadmin"]

        reserved_fields = [
            "notes",
            "resultat_placement",
            "responsable_placement",
            "date_placement",
            "entreprise_placement",
            "contrat_signe",
            "entreprise_validee",
            "courrier_rentree",
            "vu_par",
            "admissible",
            "entretien_done",
            "test_is_ok",
            "communication",
            "experience",
            "csp",
            "nb_appairages",
            "nb_prospections",
        ]
        if not is_staff_or_admin:
            for field in reserved_fields:
                data.pop(field, None)

        return data


# ─────────────────────────────────────────────────────────────────────────────
# Candidat (liste)
# ─────────────────────────────────────────────────────────────────────────────
@extend_schema_serializer()
class CandidatListSerializer(serializers.ModelSerializer):
    formation_info = FormationLiteSerializer(source="formation", read_only=True)
    last_appairage = serializers.SerializerMethodField()  # ✅ dernier appairage pour la table
    nom_complet = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True)
    nb_appairages = serializers.IntegerField(source="nb_appairages_calc", read_only=True)
    nb_prospections = serializers.IntegerField(source="nb_prospections_calc", read_only=True)
    role_utilisateur = serializers.CharField(read_only=True)
    ateliers_resume = serializers.CharField(read_only=True)
    peut_modifier = serializers.SerializerMethodField()
    cv_statut_display = serializers.CharField(read_only=True)
    ateliers_counts = serializers.SerializerMethodField()
    centre_id = serializers.IntegerField(source="formation.centre_id", read_only=True)
    centre_nom = serializers.CharField(source="formation.centre.nom", read_only=True)

    # ✅ Libellés visibles même pour non-staff
    responsable_placement_nom = serializers.SerializerMethodField()
    entreprise_placement_nom = serializers.SerializerMethodField()
    entreprise_validee_nom = serializers.SerializerMethodField()
    vu_par_nom = serializers.SerializerMethodField()
    resultat_placement_display = serializers.SerializerMethodField()

    class Meta:
        model = Candidat
        fields = [
            "id",
            "nom",
            "prenom",
            "nom_complet",
            "email",
            "telephone",
            "ville",
            "code_postal",
            "age",
            "statut",
            "cv_statut",
            "cv_statut_display",
            "formation",
            "centre_nom",
            "centre_id",
            "formation_info",
            "centre_nom",
            "evenement",
            "notes",
            "origine_sourcing",
            "date_inscription",
            "date_naissance",
            "rqth",
            "type_contrat",
            "disponibilite",
            "permis_b",
            "communication",
            "experience",
            "csp",
            "entretien_done",
            "test_is_ok",
            "admissible",
            "compte_utilisateur",
            "role_utilisateur",
            "responsable_placement",
            "date_placement",
            "entreprise_placement",
            "resultat_placement",
            "entreprise_validee",
            "contrat_signe",
             "inscrit_gespers",
            "courrier_rentree",
            "date_rentree",
            "vu_par",
            "nb_appairages",
            "nb_prospections",
            "ateliers_resume",
            "ateliers_counts",  
            "peut_modifier",
            "numero_osia",
            # ✅ nouveaux champs libellés
            "responsable_placement_nom",
            "entreprise_placement_nom",
            "entreprise_validee_nom",
            "vu_par_nom",
            "resultat_placement_display",
            # ✅ dernier appairage prêt pour l’UI
            "last_appairage",
        ]

    # ------- label getters -------
    def get_centre_nom(self, obj):
        f = getattr(obj, "formation", None)
        c = getattr(f, "centre", None) if f else None
        return getattr(c, "nom", None)

    def get_ateliers_counts(self, obj):
        return _ateliers_counts_for(obj)
    
    def get_responsable_placement_nom(self, obj):
        return _user_display(getattr(obj, "responsable_placement", None))

    def get_entreprise_placement_nom(self, obj):
        p = getattr(obj, "entreprise_placement", None)
        return getattr(p, "nom", None) if p else None

    def get_entreprise_validee_nom(self, obj):
        p = getattr(obj, "entreprise_validee", None)
        return getattr(p, "nom", None) if p else None

    def get_vu_par_nom(self, obj):
        return _user_display(getattr(obj, "vu_par", None))

    def get_resultat_placement_display(self, obj):
        return obj.get_resultat_placement_display() if getattr(obj, "resultat_placement", None) else None

    def get_last_appairage(self, obj):
        last = (
            obj.appairages.order_by("-date_appairage", "-pk")
            .select_related("partenaire", "created_by")
            .first()
        )
        return AppairageLiteSerializer(last, context=self.context).data if last else None
    # -----------------------------

    def get_peut_modifier(self, instance):
        request = self.context.get("request")
        user = request.user if request and request.user.is_authenticated else None
        if not user:
            return False
        return user.role in ["admin", "superadmin", "staff"] or instance.compte_utilisateur == user

    def to_representation(self, instance):
        data = super().to_representation(instance)

        nom, prenom, nom_complet = _normalize_nom_prenom(instance)
        data["nom"] = nom
        data["prenom"] = prenom
        data["nom_complet"] = nom_complet

        request = self.context.get("request")
        user = request.user if request and request.user.is_authenticated else None
        role = getattr(user, "role", None)
        is_staff_or_admin = role in ["staff", "admin", "superadmin"]

        reserved_fields = [
            "notes",
            "resultat_placement",
            "responsable_placement",
            "date_placement",
            "entreprise_placement",
            "contrat_signe",
            "entreprise_validee",
            "courrier_rentree",
            "vu_par",
            "admissible",
            "entretien_done",
            "test_is_ok",
            "communication",
            "experience",
            "csp",
            "nb_appairages",
            "nb_prospections",
        ]
        if not is_staff_or_admin:
            for field in reserved_fields:
                data.pop(field, None)

        return data


# ─────────────────────────────────────────────────────────────────────────────
# Create/Update
# ─────────────────────────────────────────────────────────────────────────────
class CandidatCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidat
        fields = "__all__"
        read_only_fields = [
            "id",
            "date_inscription",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]

    def validate(self, data):
        request = self.context.get("request")
        user = request.user if request else None
        if not request or not user or not user.is_authenticated:
            raise exceptions.PermissionDenied("Authentification requise.")

        restricted_fields = [
            "admissible",
            "notes",
            "resultat_placement",
            "responsable_placement",
            "date_placement",
            "entreprise_placement",
            "contrat_signe",
            "entreprise_validee",
            "courrier_rentree",
            "vu_par",
        ]
        if user.role not in ["admin", "superadmin"]:
            for field in restricted_fields:
                if field in data:
                    raise serializers.ValidationError(
                        {field: "Ce champ ne peut être modifié que par un administrateur."}
                    )

        if "numero_osia" in data:
            if user.role not in ["admin", "superadmin", "staff"]:
                raise serializers.ValidationError({"numero_osia": "Non autorisé."})
            if self.instance and self.instance.numero_osia and data["numero_osia"] != self.instance.numero_osia:
                raise serializers.ValidationError({"numero_osia": "Déjà attribué et non modifiable."})

        contrat_signe_val = data.get("contrat_signe", getattr(self.instance, "contrat_signe", None))
        numero_osia_val = data.get("numero_osia", getattr(self.instance, "numero_osia", None))
        SIGNED_VALUES = {"oui", "signed", "valide"}
        if isinstance(contrat_signe_val, str) and contrat_signe_val.lower() in SIGNED_VALUES and not numero_osia_val:
            raise serializers.ValidationError({"numero_osia": "Requis quand le contrat est signé."})

        return data

    def validate_formation(self, value):
        request = self.context.get("request")
        user = request.user if request and request.user.is_authenticated else None
        if not user or user.role not in ["admin", "superadmin", "staff"]:
            raise serializers.ValidationError("Seul le staff peut créer/modifier la formation d’un candidat.")
        return value


# ─────────────────────────────────────────────────────────────────────────────
# Meta
# ─────────────────────────────────────────────────────────────────────────────
@extend_schema_serializer()
class CandidatMetaSerializer(serializers.Serializer):
    def to_representation(self, _):
        return {
            "statut_choices": [{"value": k, "label": v} for k, v in Candidat.StatutCandidat.choices],
            "cv_statut_choices": [{"value": k, "label": v} for k, v in Candidat.CVStatut.choices],
            "type_contrat_choices": [{"value": k, "label": v} for k, v in Candidat.TypeContrat.choices],
            "disponibilite_choices": [{"value": k, "label": v} for k, v in Candidat.Disponibilite.choices],
            "resultat_placement_choices": [{"value": k, "label": v} for k, v in ResultatPlacementChoices.choices],
            "contrat_signe_choices": [{"value": k, "label": v} for k, v in Candidat.ContratSigne.choices],
            "niveau_choices": [{"value": val, "label": f"{val} ★"} for val, _ in NIVEAU_CHOICES],
            "centre_choices": [{"value": c.id, "label": c.nom} for c in Centre.objects.order_by("nom").only("id", "nom")],
            "formation_choices": [
                {
                    "value": f.id,
                    "label": f"{f.nom}" + (f" — {f.num_offre}" if f.num_offre else ""),
                }
                for f in (
                    Formation.objects.select_related("centre")
                    .only("id", "nom", "num_offre", "centre__nom")
                    .order_by("nom")
                )
            ],
        }


# ─────────────────────────────────────────────────────────────────────────────
# Historique placement
# ─────────────────────────────────────────────────────────────────────────────
@extend_schema_serializer()
class HistoriquePlacementSerializer(serializers.ModelSerializer):
    candidat_nom = serializers.CharField(source="candidat.nom_complet", read_only=True)
    entreprise_nom = serializers.CharField(source="entreprise.nom", read_only=True)
    responsable_nom = serializers.CharField(source="responsable.get_full_name", read_only=True)

    class Meta:
        model = HistoriquePlacement
        fields = [
            "id",
            "candidat",
            "candidat_nom",
            "entreprise",
            "entreprise_nom",
            "responsable",
            "responsable_nom",
            "resultat",
            "date_placement",
            "commentaire",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "candidat_nom", "entreprise_nom", "responsable_nom"]


class HistoriquePlacementCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoriquePlacement
        fields = [
            "candidat",
            "entreprise",
            "responsable",
            "resultat",
            "date_placement",
            "commentaire",
        ]


@extend_schema_serializer()
class HistoriquePlacementMetaSerializer(serializers.Serializer):
    resultat_choices = serializers.SerializerMethodField()

    def get_resultat_choices(self, _):
        return [{"value": k, "label": v} for k, v in ResultatPlacementChoices.choices]


# ─────────────────────────────────────────────────────────────────────────────
# Query params
# ─────────────────────────────────────────────────────────────────────────────
class LabelOrValueChoiceField(serializers.ChoiceField):
    """Accepte value ('accompagnement') ou label ('En accompagnement', insensible à la casse)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._label2value = {str(label).lower(): value for value, label in self.choices.items()}

    def to_internal_value(self, data):
        s = str(data)
        if s in self.choices:
            return s
        v = self._label2value.get(s.lower())
        if v is not None:
            return v
        return super().to_internal_value(data)


class CandidatQueryParamsSerializer(serializers.Serializer):
    # filtres simples
    statut = LabelOrValueChoiceField(choices=dict(Candidat.StatutCandidat.choices), required=False)
    type_contrat = LabelOrValueChoiceField(choices=dict(Candidat.TypeContrat.choices), required=False)
    cv_statut = LabelOrValueChoiceField(choices=dict(Candidat.CVStatut.choices), required=False)

    # variantes CSV si présentes côté FilterSet
    statut__in = serializers.CharField(required=False)
    type_contrat__in = serializers.CharField(required=False)
    cv_statut__in = serializers.CharField(required=False)

    # alias camelCase éventuels
    typeContrat = serializers.CharField(required=False)
    cvStatut = serializers.CharField(required=False)

    def _labels_to_values(self, values, choices_dict):
        label2value = {str(lbl).lower(): val for val, lbl in choices_dict.items()}
        out = []
        for item in values:
            s = str(item)
            if s in choices_dict:
                out.append(s)
            else:
                out.append(label2value.get(s.lower(), s))
        return out

    def validate(self, attrs):
        # alias camelCase → snake_case
        if "typeContrat" in attrs and "type_contrat" not in attrs:
            attrs["type_contrat"] = attrs.pop("typeContrat")
        if "cvStatut" in attrs and "cv_statut" not in attrs:
            attrs["cv_statut"] = attrs.pop("cvStatut")

        # normalise les champs __in si fournis en CSV (labels ou values)
        for key, choices in (
            ("statut__in", dict(Candidat.StatutCandidat.choices)),
            ("type_contrat__in", dict(Candidat.TypeContrat.choices)),
            ("cv_statut__in", dict(Candidat.CVStatut.choices)),
        ):
            if key in attrs and isinstance(attrs[key], str):
                raw = [x.strip() for x in attrs[key].split(",") if x.strip()]
                attrs[key] = self._labels_to_values(raw, choices)

        return attrs
