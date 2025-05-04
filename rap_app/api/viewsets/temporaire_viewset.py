from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema


@extend_schema(
    tags=["🔐 Authentification"],
    summary="Vérifier la validité du token et le rôle",
    description="""
        Cette vue permet de vérifier si un token d’authentification (JWT ou DRF Token) est valide,
        et retourne les informations du compte utilisateur connecté, y compris son rôle.

        🔒 Requiert un token d’authentification valide.
    """,
    responses={
        200: {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "message": {"type": "string"},
                "user_id": {"type": "integer"},
                "username": {"type": "string"},
                "email": {"type": "string"},
                "role": {"type": "string"},
                "is_staff": {"type": "boolean"},
                "is_superuser": {"type": "boolean"},
            }
        }
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
