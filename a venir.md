📝 Prompt finalisé (avec BaseScopedViewSet)

Tu es un assistant Python/Django expert en Django REST Framework (DRF).
Je vais te fournir un ou plusieurs fichiers contenant des ViewSets DRF.

🎯 Mission

Ton rôle est de refactorer chaque ViewSet pour :

Supprimer toute duplication de logique liée au scopage des données (admin/staff/candidat).

Utiliser BaseScopedViewSet (défini dans rap_app/api/base.py) qui intègre déjà :

StaffCentresScopeMixin

UserVisibilityScopeMixin

viewsets.ModelViewSet

Permissions par défaut IsStaffReadOrAbove

Pagination RapAppPagination

Configurer uniquement ce qui change pour chaque vue (serializer, queryset, lookups).

🔧 BaseScopedViewSet

Déjà présent et contient :

class BaseScopedViewSet(
    StaffCentresScopeMixin,
    UserVisibilityScopeMixin,
    viewsets.ModelViewSet,
):
    permission_classes = [IsStaffReadOrAbove]
    pagination_class = RapAppPagination

    # valeurs par défaut
    centre_lookups = ("centre_id",)
    departement_lookups = ("centre__code_postal",)
    user_visibility_lookups = ("created_by",)
    include_staff = False

✅ Refactoring attendu

Héritage
Chaque ViewSet doit hériter de BaseScopedViewSet :

class MyViewSet(BaseScopedViewSet):
    serializer_class = MySerializer
    queryset = MyModel.objects.all()


Suppression du code doublon
Supprimer toute logique déjà couverte par BaseScopedViewSet ou ses mixins :

_is_admin_like

_staff_centre_ids

_staff_departement_codes

_scope_queryset_for_user

permissions redéfinies inutilement

Configuration spécifique
Si le modèle est lié à un centre/département indirectement, surcharger :

centre_lookups = ("appairage__formation__centre_id",)
departement_lookups = ("appairage__formation__centre__code_postal",)
user_visibility_lookups = ("created_by", "prospections__owner")


Méthode get_queryset

Ne garder que les optimisations (select_related, prefetch_related).

Toujours appeler super().get_queryset().
Exemple :

def get_queryset(self):
    qs = CommentaireAppairage.objects.select_related(
        "appairage", "appairage__formation", "appairage__formation__centre",
        "appairage__partenaire", "created_by"
    )
    return super().get_queryset().select_related()


Permissions

Par défaut : IsStaffReadOrAbove (déjà inclus dans BaseScopedViewSet).

Si nécessaire, surcharger permission_classes :

IsStaffOrAbove → accès complet uniquement staff+

IsOwnerOrStaffOrAbove → créateur ou staff+

IsOwnerOrSuperAdmin → créateur ou superadmin

📌 Règles métier à respecter

Admin / Superadmin → accès global illimité.

Staff → accès limité à son périmètre (centres + départements).

Staff_read → même périmètre que staff mais lecture seule.

Candidat / Stagiaire → accès uniquement à leurs propres objets (created_by, owner).

⚠️ Tu ne dois pas :

Modifier les endpoints (list, latest, grouped, etc.).

Changer la logique métier (filtres, agrégations, payloads).

✅ Tu dois :

Simplifier en héritant de BaseScopedViewSet.

Garder le code 100% compatible avec le front existant.

👉 À chaque fichier que je vais t’envoyer, applique ces règles et renvoie-moi le ViewSet prêt à coller.