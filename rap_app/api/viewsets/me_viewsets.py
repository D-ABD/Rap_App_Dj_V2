from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse

from ..serializers.base_serializers import EmptySerializer

from ...models.custom_user import CustomUser
from ...models.logs import LogUtilisateur
from ..serializers.user_profil_serializers import CustomUserSerializer, RoleChoiceSerializer


class MeAPIView(APIView):
    serializer_class = EmptySerializer

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Afficher son profil",
        tags=["Utilisateur"],
        responses={200: OpenApiResponse(response=CustomUserSerializer)},
    )
    def get(self, request):
        user = request.user
        return Response(
            {
                "success": True,
                "message": "Profil récupéré avec succès.",
                "data": user.to_serializable_dict(include_sensitive=True),
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Mettre à jour son profil",
        tags=["Utilisateur"],
        request=CustomUserSerializer,
        responses={200: OpenApiResponse(response=CustomUserSerializer)},
    )
    def patch(self, request):
        user = request.user
        serializer = CustomUserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        LogUtilisateur.log_action(
            instance=user,
            action=LogUtilisateur.ACTION_UPDATE,
            user=user,
            details="Mise à jour de son propre profil via MeAPIView",
        )

        return Response(
            {
                "success": True,
                "message": "Profil mis à jour avec succès.",
                "data": user.to_serializable_dict(include_sensitive=True),
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Réactiver son compte",
        tags=["Utilisateur"],
        responses={200: OpenApiResponse(response=CustomUserSerializer)},
    )
    def post(self, request, *args, **kwargs):
        """
        Permet à l'utilisateur de réactiver son propre compte
        (utile si désactivation volontaire, puis retour).
        """
        user = request.user
        if user.is_active:
            return Response(
                {"success": False, "message": "Votre compte est déjà actif."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.is_active = True
        user.save(update_fields=["is_active"])

        LogUtilisateur.log_action(
            instance=user,
            action=LogUtilisateur.ACTION_UPDATE,
            user=user,
            details="Réactivation du compte via MeAPIView",
        )

        return Response(
            {
                "success": True,
                "message": "Votre compte a été réactivé avec succès.",
                "data": user.to_serializable_dict(include_sensitive=True),
            },
            status=status.HTTP_200_OK,
        )


class RoleChoicesView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Liste des rôles utilisateurs disponibles",
        description="Retourne tous les rôles utilisables avec leurs identifiants et libellés.",
        responses={200: OpenApiResponse(response=RoleChoiceSerializer(many=True))},
        tags=["Utilisateur"],
    )
    def get(self, request):
        data = [{"value": value, "label": label} for value, label in CustomUser.ROLE_CHOICES]
        return Response(data, status=status.HTTP_200_OK)
