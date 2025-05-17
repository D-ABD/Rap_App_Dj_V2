

# ✅ Demande d’assistance pour API Django REST – Niveau professionnel

Je développe une application Django avec un frontend React confié à un développeur débutant.  
Je souhaite que tu m’assistes pour générer des **serializers, viewsets, URLs et tests unitaires** pour chaque modèle.

---

## 🎯 Objectif principal

Créer une **API robuste, auto-documentée et exploitable sans ambiguïté**, sans que le développeur frontend ait besoin d’accéder aux modèles backend.

---

## ✅ Attentes détaillées

### 🔐 Permissions, validations & robustesse

- Gestion explicite des **statuts HTTP** (201, 400, 403, 404…)
- Messages personnalisés et clairs :
  - ✅ `"Formation créée avec succès."`
  - ❌ `"Création échouée : le champ 'statut' est requis."`
- Validation stricte des champs obligatoires.
- **Retour structuré** pour chaque réponse API :
```json
{
  "success": false,
  "message": "Le champ 'nom' est requis.",
  "data": null
}
```

---

### 🧩 Serializers

- Basés sur `to_serializable_dict()` (si disponible) ou équivalent, pour refléter :
  - Méthodes métier
  - Propriétés enrichies
  - Champs calculés
- **Affichage lisible** pour les champs à choix : `*_display`
- Affichage enrichi des ForeignKeys :
  - Ex : `centre_id`, `centre_nom`
- Gestion des **ManyToMany** avec détails lisibles si nécessaire
- Ajout de **`help_text`** pour chaque champ (utilisé par Swagger)
- Intégration des validations définies dans `clean()` ou logique métier
- **Inclure les champs standards** : `id`, `created_at`, `updated_at`, `created_by`, `updated_by`, `is_active`

---

### 🚀 ViewSets
surcharger les méthodes create, update, destroy, retrieve, list dans ton StatutViewSet
- CRUD complet : `list`, `retrieve`, `create`, `update`, `destroy`
- Ajout des **méthodes personnalisées** via `@action` :
  - Ex : `changer_statut()`, `dupliquer()`, `relancer()`, `ajouter_document()`
- **Retour structuré** comme suit :
```json
{
  "success": true,
  "message": "Formation mise à jour avec succès.",
  "data": { ... }
}
```
Gestion des prmissions dans le viewset

Pagination personnalisée:


# rap_app/api/paginations.py

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class RapAppPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "success": True,
            "message": "Liste paginée des résultats.",
            "data": {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data
            }
        })



# rap_app/api/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsSuperAdminOnly(BasePermission):
    """
    Autorise uniquement les superadmins à accéder à cette vue.
    """
    message = "Accès réservé aux superadmins uniquement."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == 'superadmin'
        )


class IsAdmin(BasePermission):
    """
    Autorise uniquement les administrateurs (staff, admin, superadmin) à accéder à cette vue.
    """
    message = "Accès réservé aux membres du staff, admins ou superadmins."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in ['staff', 'admin', 'superadmin']
        )


class ReadWriteAdminReadStaff(BasePermission):
    """
    Lecture : autorisée pour staff, admin, superadmin.
    Écriture : réservée à admin et superadmin uniquement.
    """
    message = "Lecture autorisée pour le staff. Modifications réservées aux admins ou superadmins."

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            self.message = "Authentification requise."
            return False

        role = getattr(user, 'role', None)

        if request.method in SAFE_METHODS:
            if role in ['staff', 'admin', 'superadmin']:
                return True
            self.message = "Lecture réservée au staff, admins ou superadmins."
            return False

        if role in ['admin', 'superadmin']:
            return True

        self.message = "Seuls les admins ou superadmins peuvent modifier cette ressource."
        return False


class IsStaffOrAbove(BasePermission):
    """
    Autorise uniquement le staff, les admins ou les superadmins à accéder à la vue.
    """
    message = "Accès réservé au staff, aux admins ou aux superadmins."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in ['staff', 'admin', 'superadmin']
        )


class ReadOnlyOrAdmin(BasePermission):
    """
    Tout le monde peut lire (GET, HEAD, OPTIONS), seuls les admins ou superadmins peuvent modifier.
    """
    message = "Lecture publique. Modifications réservées aux admins ou superadmins."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return (
            request.user.is_authenticated and
            request.user.role in ['admin', 'superadmin']
        )


class IsOwnerOrSuperAdmin(BasePermission):
    """
    Autorise l'accès si l'utilisateur est le propriétaire OU superadmin.
    """
    message = "Vous ne pouvez accéder qu'à vos propres données, sauf si vous êtes superadmin."

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            self.message = "Authentification requise."
            return False

        if getattr(user, 'role', '') == 'superadmin':
            return True

        return getattr(obj, 'user', None) == user or getattr(obj, 'owner', None) == user


class IsOwnerOrStaffOrAbove(BasePermission):
    """
    Autorise l'accès si l'utilisateur est le propriétaire OU staff/admin/superadmin.
    """
    message = "Accès réservé au propriétaire ou aux membres du staff, admin ou superadmin."

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            self.message = "Authentification requise."
            return False

        if getattr(user, 'role', '') in ['staff', 'admin', 'superadmin']:
            return True

        return getattr(obj, 'user', None) == user or getattr(obj, 'owner', None) == user
 
---

### 📘 Swagger / drf-spectacular

- Utiliser systématiquement `@extend_schema` :
  - `summary`, `description`, `request`, `responses`, `examples`
- Chaque endpoint doit être **clairement testable via Swagger UI**
- Exemple attendu dans Swagger :
  - ✅ Exemple de réponse de succès
  - ❌ Exemple de validation échouée

---

### ✅ Tests unitaires

- Générer des **tests pour chaque serializer et viewset** :
  - ✔ Cas de succès
  - ❌ Cas de validation échouée
  - 🔄 Cas de mise à jour partielle
Vérifier systématiquement que les actions CRUD sont bien journalisées dans LogUtilisateur, avec les bons attributs :
* action ("création", "modification", "suppression")
* created_by
* content_type, object_id

Exemple de vérification recommandée :

log = LogUtilisateur.objects.filter(
    content_type=ContentType.objects.get_for_model(ObjetConcerné),
    object_id=obj.id,
    action="modification",
    created_by=utilisateur
)
self.assertTrue(log.exists(), "Log de modification non détecté.")
- Mock des permissions, actions custom et logique métier si nécessaire
-  privilégiez TestCase pour les tests de serializers (plus légers et ciblés), et réservez APITestCase aux tests d'endpoints.
---

### 🧱 BaseModel

Tous les modèles héritent d’un BaseModel contenant :
```python
id, created_at, updated_at, created_by, updated_by, is_active
```

---
## Exemple de serializes, viewset et tests

# serializers/custom_user_serializers.py

from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from django.utils.translation import gettext_lazy as _

from ...models.custom_user import CustomUser

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name="Utilisateur standard",
            value={
                "email": "jane.doe@example.com",
                "username": "janedoe",
                "first_name": "Jane",
                "last_name": "Doe",
                "phone": "0601020304",
                "role": "stagiaire",
                "bio": "Stagiaire motivée",
                "avatar": None
            },
            response_only=False,
        ),
    ]
)
class CustomUserSerializer(serializers.ModelSerializer):
    """
    🎯 Serializer principal pour les utilisateurs.
    Utilise `to_serializable_dict()` pour exposer les données enrichies.
    """

    role_display = serializers.CharField(source='get_role_display', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    avatar_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "id", "email", "username", "first_name", "last_name", "phone", "bio",
            "avatar", "avatar_url", "role", "role_display",
            "is_active", "date_joined", "full_name"
        ]
        read_only_fields = ["id", "avatar_url", "role_display", "date_joined", "full_name"]
        extra_kwargs = {
            "email": {
                "required": True,
                "error_messages": {
                    "required": _("Création échouée : l'adresse email est requise."),
                    "blank": _("Création échouée : l'adresse email ne peut pas être vide."),
                },
                "help_text": "Adresse email unique utilisée pour se connecter",
            },
            "username": {
                "required": True,
                "error_messages": {
                    "required": _("Création échouée : le nom d'utilisateur est requis."),
                    "blank": _("Création échouée : le nom d'utilisateur ne peut pas être vide."),
                },
                "help_text": "Nom d'utilisateur unique pour cet utilisateur",
            },
            "role": {
                "help_text": "Rôle de l'utilisateur dans l'application",
            },
            "avatar": {
                "help_text": "Image de profil de l'utilisateur",
            },
            "bio": {
                "help_text": "Texte de présentation ou bio",
            },
            "phone": {
                "help_text": "Numéro de téléphone portable",
            },
        }

    def get_avatar_url(self, obj):
        """
        🖼️ Retourne l'URL complète de l'avatar de l'utilisateur.
        """
        return obj.avatar_url()

    def to_representation(self, instance):
        """
        🎁 Structure uniforme de sortie API
        """
        return {
            "success": True,
            "message": "Utilisateur récupéré avec succès.",
            "data": instance.to_serializable_dict(include_sensitive=True),
        }

    def create(self, validated_data):
        """
        ➕ Crée un utilisateur à partir des données validées
        """
        user = CustomUser.objects.create_user(**validated_data)
        return user  # ⛔ Pas de dictionnaire ici


    def update(self, instance, validated_data):
        """
        ✏️ Mise à jour d'un utilisateur
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return {
            "success": True,
            "message": "Utilisateur mis à jour avec succès.",
            "data": instance.to_serializable_dict(include_sensitive=True),
        }
-----
from rest_framework import viewsets, status, permissions, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from ..permissions import ReadWriteAdminReadStaff
from ..serializers.user_profil_serializers import CustomUserSerializer
from ...models.custom_user import CustomUser
from ...models.logs import LogUtilisateur


@extend_schema_view(
    list=extend_schema(
        summary="Liste des utilisateurs",
        description="Récupère tous les utilisateurs actifs, avec filtrage, recherche et tri.",
        responses={200: OpenApiResponse(response=CustomUserSerializer)},
    ),
    retrieve=extend_schema(
        summary="Détail d'un utilisateur",
        description="Récupère les informations détaillées d’un utilisateur par ID.",
        responses={200: OpenApiResponse(response=CustomUserSerializer)},
    ),
    create=extend_schema(
        summary="Créer un utilisateur",
        description="Crée un nouvel utilisateur avec un rôle, un email et d'autres champs.",
        responses={201: OpenApiResponse(description="Utilisateur créé avec succès.")},
    ),
    update=extend_schema(
        summary="Mettre à jour un utilisateur",
        description="Modifie les champs d’un utilisateur existant.",
        responses={200: OpenApiResponse(description="Utilisateur mis à jour avec succès.")},
    ),
    destroy=extend_schema(
        summary="Supprimer un utilisateur",
        description="Supprime logiquement un utilisateur (is_active = False).",
        responses={204: OpenApiResponse(description="Utilisateur supprimé avec succès.")},
    ),
)
class CustomUserViewSet(viewsets.ModelViewSet):
    """
    👤 ViewSet complet pour la gestion des utilisateurs.
    Fournit les actions CRUD + une action `me` pour l’utilisateur connecté.
    """

    queryset = CustomUser.objects.filter(is_active=True)
    serializer_class = CustomUserSerializer
    permission_classes = [ReadWriteAdminReadStaff]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["email", "username", "first_name", "last_name"]
    ordering_fields = ["email", "date_joined", "role"]
    ordering = ["-date_joined"]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_DELETE,
            user=request.user,
            details="Suppression logique de l'utilisateur"
        )
        return Response({
            "success": True,
            "message": "Utilisateur supprimé avec succès.",
            "data": None
        }, status=status.HTTP_204_NO_CONTENT)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        # Journalisation
        from ...models.logs import LogUtilisateur
        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_CREATE,
            user=request.user,
            details="Création d'un nouvel utilisateur"
        )

        return Response({
            "success": True,
            "message": "Utilisateur créé avec succès.",
            "data": instance.to_serializable_dict(include_sensitive=True)
        }, status=status.HTTP_201_CREATED)


    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        result = serializer.update(instance, serializer.validated_data)

        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_UPDATE,
            user=request.user,
            details="Mise à jour d'un utilisateur"
        )

        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="me", permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        user = request.user
        return Response({
            "success": True,
            "message": "Profil utilisateur chargé avec succès.",
            "data": user.to_serializable_dict(include_sensitive=True)
        })

    @action(detail=False, methods=["get"], url_path="roles", permission_classes=[permissions.IsAuthenticated])
    @extend_schema(
        summary="Liste des rôles utilisateurs",
        description="Retourne tous les rôles disponibles dans l'application, sous forme clé/valeur.",
        responses={200: OpenApiResponse(
            response=dict,
            description="Rôles disponibles pour la création ou modification d’un utilisateur.",
            examples=[
                OpenApiResponse(
                    description="Exemple de réponse",
                    response={
                        "success": True,
                        "message": "Liste des rôles récupérée avec succès.",
                        "data": {
                            "admin": "Administrateur",
                            "stagiaire": "Stagiaire",
                            "superadmin": "Super administrateur",
                            "staff": "Membre du staff",
                            "test": "Test"
                        }
                    }
                )
            ]
        )}
    )
    def roles(self, request):
        return Response({
            "success": True,
            "message": "Liste des rôles récupérée avec succès.",
            "data": CustomUser.get_role_choices_display()
        })
-----
# tests/test_custom_user_serializers.py

from django.test import TestCase
from ...models.custom_user import CustomUser
from ...api.serializers.user_profil_serializers import CustomUserSerializer

class CustomUserSerializerTestCase(TestCase):
    def setUp(self):
        self.valid_data = {
            "email": "test@example.com",
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "phone": "0601020304",
            "role": CustomUser.ROLE_STAGIAIRE,
            "bio": "Utilisateur de test",
        }

    def test_serializer_valid_data(self):
        """
        ✅ Test de création valide avec données complètes
        """
        serializer = CustomUserSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_serializer_missing_email(self):
        """
        ❌ Test d'échec si l'email est manquant
        """
        data = self.valid_data.copy()
        data.pop("email")
        serializer = CustomUserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)
        self.assertIn("Création échouée", serializer.errors["email"][0])

    def test_serializer_invalid_role(self):
        """
        ❌ Test d'échec si le rôle est invalide
        """
        data = self.valid_data.copy()
        data["role"] = "invalide"
        serializer = CustomUserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("role", serializer.errors)

    def test_serializer_empty_username(self):
        """
        ❌ Test d'échec si le nom d'utilisateur est vide
        """
        data = self.valid_data.copy()
        data["username"] = ""
        serializer = CustomUserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("username", serializer.errors)
        self.assertIn("ne peut pas être vide", serializer.errors["username"][0])

    def test_serializer_serialized_output_structure(self):
        """
        ✅ Vérifie que le format de sortie respecte le schéma avec `success`, `message`, `data`
        """
        user = CustomUser.objects.create_user(**self.valid_data)
        serializer = CustomUserSerializer(instance=user)
        output = serializer.data
        self.assertIn("success", output)
        self.assertIn("message", output)
        self.assertIn("data", output)
        self.assertTrue(output["success"])
        self.assertIsInstance(output["data"], dict)
-------
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.contenttypes.models import ContentType
from ...models.custom_user import CustomUser
from ...models.logs import LogUtilisateur


class CustomUserViewSetTestCase(APITestCase):
    def setUp(self):
        self.password = "StrongPass123"
        self.user = CustomUser.objects.create_user(
            email="admin@example.com",
            username="admin",
            password=self.password,
            role=CustomUser.ROLE_ADMIN,
            is_staff=True
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        self.list_url = reverse("user-list")
        self.me_url = reverse("user-me")
        self.roles_url = reverse("user-roles")

    def test_list_users(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("data", response.data)
        self.assertTrue(response.data["success"])

    def test_create_user(self):
        data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "role": "stagiaire",
            "phone": "0606060606"
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["email"], data["email"])

        # Vérification du log de création
        created_user_id = response.data["data"]["id"]
        log = LogUtilisateur.objects.filter(
            content_type=ContentType.objects.get_for_model(CustomUser),
            object_id=created_user_id,
            action__icontains="création",
            created_by=self.user
        )
        self.assertTrue(log.exists(), "Log de création non détecté.")

    def test_retrieve_user(self):
        response = self.client.get(reverse("user-detail", args=[self.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["email"], self.user.email)

    def test_update_user(self):
        url = reverse("user-detail", args=[self.user.id])
        data = {"first_name": "Modifié"}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["first_name"], "Modifié")

        # Vérification du log de modification
        log = LogUtilisateur.objects.filter(
            content_type=ContentType.objects.get_for_model(CustomUser),
            object_id=self.user.pk,
            action__icontains="modification",
            created_by=self.user
        )
        self.assertTrue(log.exists(), "Log de modification non détecté.")

    def test_delete_user_sets_is_active_false(self):
        url = reverse("user-detail", args=[self.user.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

        # Vérification du log de suppression
        log = LogUtilisateur.objects.filter(
            content_type=ContentType.objects.get_for_model(CustomUser),
            object_id=self.user.pk,
            action__icontains="suppression",
            created_by=self.user
        )
        self.assertTrue(log.exists(), "Log de suppression non détecté.")

    def test_me_endpoint(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["email"], self.user.email)

    def test_roles_endpoint(self):
        response = self.client.get(self.roles_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("stagiaire", response.data["data"])
        self.assertTrue(response.data["success"])
 
### 📂 Organisation des fichiers

```
serializers/<model>_serializers.py  
viewsets/<model>_viewsets.py  
tests/test_<model>_serializers.py  
tests/test_<model>_viewsets.py  
urls/<model>_urls.py  
```

# Import relatif clair 
from ..models import Commentaire, Formation, Centre
from ..api.serializers import CommentaireSerializer
from ..api.viewsets.logs_viewsets import LogUtilisateurViewSet  
# Exception pour les dépendances croisées
---

## 📋 Ordre logique recommandé pour traitement des modèles

1. `CustomUser` – (authentification, rôles, login/logout/me)
2. `Centre` – (base des relations)
3. `Statut`, `TypeOffre` – (référentiels)
4. `Formation` – (modèle pivot)
5. `Document` – (lié à Formation)
6. `Evenement` – (lié à Formation)
7. `Commentaire` – (lié à Formation)
8. `Partenaire`
9. `Prospection`, `HistoriqueProspection`
10. `Rapport`
11. `VAE`, `HistoriqueStatutVAE`
12. `SuiviJury`
13. `PrepaCompGlobal`
14. `LogUtilisateur`

---

## 🔄 Optionnels (à discuter)

- 🌐 Filtres via `DjangoFilterBackend`, `SearchFilter`, `OrderingFilter`
- 📥 Endpoints d’import/export (CSV, Excel…)
- ⏱️ Pagination, cache, throttling
- 📁 Gestion de l’upload de fichiers (avec validation MIME, taille…) 



Verifier l'ajout de created_at et created_by, en lecture seule, car ils sont dans base_model
 