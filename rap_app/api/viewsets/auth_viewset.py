from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from drf_spectacular.utils import extend_schema, OpenApiExample
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    🎯 Personnalise le serializer JWT pour utiliser le champ `email` à la place de `username`
    """
    username_field = User.EMAIL_FIELD  # ← utilise le champ email

    def validate(self, attrs):
        attrs['username'] = attrs.get('email')  # ✅ remplace "username" par "email"
        return super().validate(attrs)


class EmailTokenRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class EmailTokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


@extend_schema(
    tags=["Utilisateurs"],
    summary="Connexion avec email et mot de passe",
    description="Retourne un access token (JWT) et un refresh token.",
    request=EmailTokenRequestSerializer,
    responses={200: EmailTokenResponseSerializer},
    examples=[
        OpenApiExample(
            name="Requête valide",
            value={"email": "admin@example.com", "password": "motdepasse"},
            request_only=True
        ),
        OpenApiExample(
            name="Réponse réussie",
            value={
                "access": "eyJ0eXAiOiJKV1QiLCJh...",
                "refresh": "eyJ0eXAiOiJKV1QiLCJh..."
            },
            response_only=True
        ),
        OpenApiExample(
            name="Échec d’authentification",
            value={"detail": "Aucun compte actif trouvé avec les identifiants fournis"},
            response_only=True,
            status_codes=["401"]
        )
    ]
)
class EmailTokenObtainPairView(TokenObtainPairView):
    """
    🛂 Vue personnalisée JWT pour la connexion par email
    """
    serializer_class = EmailTokenObtainPairSerializer
