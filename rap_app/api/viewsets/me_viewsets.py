from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_spectacular.utils import extend_schema

from ...models.custom_user import CustomUser
from ...models.logs import LogUtilisateur
from ..serializers.user_profil_serializers import CustomUserSerializer, RoleChoiceSerializer


class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Afficher son profil",
        tags=["Utilisateur"],
        responses={200: CustomUserSerializer}
    )
    def get(self, request):
        user = request.user
        return Response({
            "success": True,
            "message": "Profil récupéré avec succès.",
            "data": user.to_serializable_dict(include_sensitive=True)
        })

    @extend_schema(
        summary="Mettre à jour son profil",
        tags=["Utilisateur"],
        request=CustomUserSerializer,
        responses={200: CustomUserSerializer}
    )
    def patch(self, request):
        user = request.user
        serializer = CustomUserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # 🔒 Journalisation de l'action utilisateur
        LogUtilisateur.log_action(
            instance=user,
            action=LogUtilisateur.ACTION_UPDATE,
            user=user,
            details="Mise à jour de son propre profil via MeAPIView"
        )

        return Response({
            "success": True,
            "message": "Profil mis à jour avec succès.",
            "data": user.to_serializable_dict(include_sensitive=True)
        }, status=status.HTTP_200_OK)
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
