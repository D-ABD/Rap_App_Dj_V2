from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse

@extend_schema(
    tags=["🔐 Authentification"],
    summary="Vérifier la validité du token et le rôle",
    description="""
        Cette vue permet de vérifier si un token d’authentification (JWT ou DRF Token) est valide,
        et retourne les informations du compte utilisateur connecté, y compris son rôle.

        🔒 Requiert un token d’authentification valide dans l'en-tête `Authorization`.
    """,
    responses={
        200: OpenApiResponse(
            description="Token valide et utilisateur authentifié",
            response={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": True},
                    "message": {"type": "string", "example": "Token valide ✅"},
                    "user_id": {"type": "integer", "example": 1},
                    "username": {"type": "string", "example": "johndoe"},
                    "email": {"type": "string", "example": "john@example.com"},
                    "role": {"type": "string", "example": "admin"},
                    "is_staff": {"type": "boolean", "example": True},
                    "is_superuser": {"type": "boolean", "example": False},
                }
            }
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test_token_view(request):
    """
    ✅ Teste si le token est valide et renvoie les informations utilisateur, y compris le rôle.
    """
    user = request.user
    role = getattr(user.profile, 'role', 'inconnu')  # évite une erreur si profil absent

    return Response({
        'success': True,
        'message': 'Token valide ✅',
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'role': role,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
    })
