from rest_framework import viewsets, status, permissions, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend

from ..permissions import ReadWriteAdminReadStaff
from ..serializers.user_profil_serializers import CustomUserSerializer, RegistrationSerializer, RoleChoiceSerializer, UserFilterSet
from ...models.custom_user import CustomUser
from ...models.logs import LogUtilisateur


@extend_schema_view(
    list=extend_schema(
        summary="Liste des utilisateurs",
        description="Récupère tous les utilisateurs actifs, avec filtrage, recherche et tri.",
        tags=["Utilisateurs"],
        responses={200: OpenApiResponse(response=CustomUserSerializer)},
    ),
    retrieve=extend_schema(
        summary="Détail d'un utilisateur",
        description="Récupère les informations détaillées d’un utilisateur par ID.",
        tags=["Utilisateurs"],
        responses={200: OpenApiResponse(response=CustomUserSerializer)},
    ),
    create=extend_schema(
        summary="Créer un utilisateur",
        description="Crée un nouvel utilisateur avec un rôle, un email et d'autres champs.",
        tags=["Utilisateurs"],
        responses={201: OpenApiResponse(description="Utilisateur créé avec succès.")},
    ),
    update=extend_schema(
        summary="Mettre à jour un utilisateur",
        description="Modifie les champs d’un utilisateur existant.",
        tags=["Utilisateurs"],
        responses={200: OpenApiResponse(description="Utilisateur mis à jour avec succès.")},
    ),
    destroy=extend_schema(
        summary="Supprimer un utilisateur",
        description="Supprime logiquement un utilisateur (is_active = False).",
        tags=["Utilisateurs"],
        responses={204: OpenApiResponse(description="Utilisateur supprimé avec succès.")},
    ),
)


class RegisterView(APIView):

    def get_permissions(self):
        return [AllowAny()]  # <-- 🔒 Ceci écrase les permissions globales
     
    def post(self, request):
        print("📥 RegisterView POST data:", request.data)
        print("🔐 User:", request.user, "- Authenticated:", request.user.is_authenticated)
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "success": True,
                "message": "Compte créé. En attente de validation.",
                "user": {
                    "email": user.email,
                }
            }, status=status.HTTP_201_CREATED)
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class CustomUserViewSet(viewsets.ModelViewSet):
    """
    👤 ViewSet complet pour la gestion des utilisateurs.
    Fournit les actions CRUD + une action `me` pour l’utilisateur connecté.
    """

    queryset = CustomUser.objects.all()      
    serializer_class = CustomUserSerializer
    permission_classes = [ReadWriteAdminReadStaff]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_class = UserFilterSet
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



    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        LogUtilisateur.log_action(
            instance=instance,
            action=LogUtilisateur.ACTION_UPDATE,
            user=request.user,
            details="Mise à jour d'un utilisateur"
        )

        return Response({
            "success": True,
            "message": "Utilisateur mis à jour avec succès.",
            "data": instance.to_serializable_dict(include_sensitive=True)
        }, status=status.HTTP_200_OK)


        return Response({
            "success": True,
            "message": "Utilisateur mis à jour avec succès.",
            "data": result
        }, status=status.HTTP_200_OK)


    @action(detail=False, methods=["get"], url_path="me", permission_classes=[permissions.IsAuthenticated])
    @extend_schema(
        summary="Mon profil utilisateur",
        description="Retourne les informations complètes de l’utilisateur actuellement connecté.",
        tags=["Utilisateurs"],
        responses={200: OpenApiResponse(response=CustomUserSerializer)}
    )
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
        tags=["Utilisateurs"],
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

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "success": True,
            "message": "Utilisateur récupéré avec succès.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="liste-simple")
    @extend_schema(
        summary="Liste simple des utilisateurs (id + nom complet)",
        description="Retourne une liste allégée des utilisateurs actifs pour les filtres (id, nom).",
        tags=["Utilisateurs"]
    )
    def liste_simple(self, request):
        users = CustomUser.objects.filter(is_active=True).only("id", "first_name", "last_name", "email").order_by("first_name")
        data = [
            {
                "id": user.id,
                "nom": f"{user.first_name} {user.last_name}".strip() or user.email
            }
            for user in users
        ]
        return Response({"success": True, "data": data})        

class RoleChoicesView(APIView):
    @extend_schema(
        responses={200: RoleChoiceSerializer(many=True)},
        summary="Liste des rôles utilisateurs disponibles",
        description="Retourne tous les rôles utilisables avec leurs identifiants et libellés."
    )
    def get(self, request):
        data = [
            {"value": value, "label": label}
            for value, label in CustomUser.ROLE_CHOICES
        ]
        return Response(data)
