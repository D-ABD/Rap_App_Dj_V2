# IsOwnerOrStaffOrAbove

from django.contrib.auth.models import User
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from ..serializers.user_profil_serializers import (
    PasswordChangeSerializer,
    UserProfileSerializer,
    UserUpdateSerializer,
    RoleUpdateSerializer,
)
from ...models.user_profil import UserProfile
from ..permissions import IsOwnerOrSuperAdmin


@extend_schema(
    tags=["Utilisateur"],
    summary="Gérer les utilisateurs et leurs profils",
    description="""
        Ce ViewSet permet :
        - à un utilisateur : de voir ou modifier **son propre profil**
        - au **superadmin** : d'accéder à tous les profils
        - aux **admins** : de changer le rôle d'un autre utilisateur (`set-role`)
        - à tout utilisateur authentifié : de modifier son mot de passe (`change-password`)
    """
)
class UserViewSet(viewsets.ModelViewSet):
    """
    API pour gérer les utilisateurs et leur profil.

    - GET /users/{id}/ : voir un profil
    - GET /users/me/ : voir son propre profil
    - POST /users/change-password/ : changer son mot de passe
    - PATCH /users/{id}/set-role/ : changer le rôle (admin uniquement)
    """

    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrSuperAdmin]

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return super().get_serializer_class()

    @extend_schema(
        summary="Voir son propre profil",
        responses={200: UserProfileSerializer}
    )
    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        """Retourne les infos du compte connecté."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        summary="Changer son mot de passe",
        request=PasswordChangeSerializer,
        responses={200: {"type": "object", "properties": {"detail": {"type": "string"}}}}
    )
    @action(detail=False, methods=['post'], url_path='change-password')
    def change_password(self, request):
        """Permet à un utilisateur de changer son mot de passe."""
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Mot de passe mis à jour avec succès."})

    @extend_schema(
        summary="Changer le rôle d’un utilisateur (admin seulement)",
        request=RoleUpdateSerializer,
        responses={200: {"type": "object", "properties": {"detail": {"type": "string"}}}}
    )
    @action(detail=True, methods=['patch'], url_path='set-role', permission_classes=[IsAdminUser])
    def set_role(self, request, pk=None):
        """
        Permet aux administrateurs de modifier le rôle d'un utilisateur.
        """
        user = self.get_object()
        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            return Response({"detail": "Profil utilisateur manquant."}, status=404)

        serializer = RoleUpdateSerializer(instance=profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Rôle mis à jour avec succès."})
