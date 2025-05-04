from django.contrib.auth.models import User
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from ..serializers.user_profil_serializers import PasswordChangeSerializer, UserProfileSerializer, UserUpdateSerializer

from ...models.user_profil import UserProfile


class UserViewSet(viewsets.ModelViewSet):
    """
    API pour gérer les utilisateurs et leur profil.

    - `retrieve` : Voir les infos d’un utilisateur
    - `me` : Voir ses propres informations
    - `change_password` : Modifier son mot de passe
    - `set_role` : Modifier le rôle d’un autre utilisateur (admin uniquement)
    """
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'update' or self.action == 'partial_update':
            return UserUpdateSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        """Retourne les infos du compte connecté."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='change-password')
    def change_password(self, request):
        """Permet à un utilisateur de changer son mot de passe."""
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Mot de passe mis à jour avec succès."})

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
