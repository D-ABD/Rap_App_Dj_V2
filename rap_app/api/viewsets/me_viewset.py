# views/me_view.py

from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..serializers.user_profil_serializers import UserProfileSerializer


@extend_schema(
    tags=["Utilisateur"],
    summary="Profil de l'utilisateur connecté",
    description="""
        Renvoie les informations du compte actuellement connecté via l'endpoint `/me/`.

        🔒 Requiert une authentification avec un token valide.
    """,
    responses={
        200: UserProfileSerializer,
        401: OpenApiResponse(description="Non authentifié - Token manquant ou invalide.")
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    """
    Vue API qui renvoie les informations du profil de l'utilisateur connecté.

    Accessible uniquement avec un token valide.
    """
    user = request.user
    serializer = UserProfileSerializer(user, context={'request': request})
    return Response(serializer.data)
