from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from ...models.user_profil import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """Sérialiseur du profil utilisateur (UserProfile)."""
    class Meta:
        model = UserProfile
        fields = ['phone', 'avatar', 'bio', 'role']
        read_only_fields = ['role']  # Pour empêcher modification sauf via endpoint admin


class UserSerializer(serializers.ModelSerializer):
    """Sérialiseur principal d'un utilisateur avec son profil étendu."""
    profile = UserProfileSerializer()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'profile']


class UserUpdateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour mise à jour des données utilisateur (hors mot de passe)."""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class PasswordChangeSerializer(serializers.Serializer):
    """Sérialiseur pour le changement de mot de passe."""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])

    def validate(self, data):
        user = self.context['request'].user
        if not user.check_password(data['old_password']):
            raise serializers.ValidationError({"old_password": "Mot de passe actuel incorrect."})
        return data

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class RoleUpdateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour mise à jour du rôle (admin-only)."""
    class Meta:
        model = UserProfile
        fields = ['role']
