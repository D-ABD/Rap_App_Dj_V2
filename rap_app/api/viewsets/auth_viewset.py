from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
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


@extend_schema(
    tags=["Utilisateurs"],
    summary="Connexion avec email et mot de passe",
    description="Retourne un token d'accès (JWT) et un refresh token à partir d'un email et d'un mot de passe.",
    request=EmailTokenObtainPairSerializer,
    responses={
        200: OpenApiExample(
            "Réponse de succès",
            value={
                "access": "eyJ0eXAiOiJKV1QiLCJh...",
                "refresh": "eyJ0eXAiOiJKV1QiLCJh..."
            },
            response_only=True
        ),
        401: OpenApiExample(
            "Échec d’authentification",
            value={"detail": "Aucun compte actif trouvé avec les identifiants fournis"},
            response_only=True,
        )
    }
)
class EmailTokenObtainPairView(TokenObtainPairView):
    """
    🛂 Vue personnalisée JWT pour connexion avec email
    """
    serializer_class = EmailTokenObtainPairSerializer
