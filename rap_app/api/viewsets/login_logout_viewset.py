from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout

from drf_spectacular.utils import extend_schema

from ..serializers.login_logout_serializers import LoginSerializer, UserSerializer


@extend_schema(
    methods=["post"],
    tags=["Authentification"],
    summary="Connexion",
    description="""
    Permet à un utilisateur de se connecter et de recevoir un token d'authentification.

    ✅ Accès public (non authentifié).
    🔐 Le token est requis ensuite pour les appels protégés.
    """,
    request=LoginSerializer,
    responses={200: UserSerializer}
)
class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)

        token, created = Token.objects.get_or_create(user=user)

        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)

@extend_schema(
    methods=["post"],
    tags=["Authentification"],
    summary="Déconnexion",
    description="""
    Permet à un utilisateur connecté de se déconnecter et d'invalider son token d'authentification.

    🔒 Requiert un token actif dans l’en-tête Authorization.
    """,
    responses={200: {"type": "object", "properties": {
        "detail": {"type": "string", "example": "Déconnexion réussie."}
    }}}
)
class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            request.user.auth_token.delete()
        except (AttributeError, Token.DoesNotExist):
            pass

        logout(request)
        return Response({"detail": "Déconnexion réussie."}, status=status.HTTP_200_OK)
