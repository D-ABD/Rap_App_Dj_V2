from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test_token_view(request):
    """
    ✅ Teste si le token JWT envoyé est valide.
    """
    # Ajout des prints pour débogage
    print(f"Token test view: user authenticated = {request.user.is_authenticated}")
    print(f"Token test view: user = {request.user}")
    print(f"Token test view: auth = {request.auth}")
    print(f"Token test view: auth payload = {getattr(request.auth, 'payload', 'No payload')}")
    
    user = request.user
    return Response({
        'success': True,
        'message': 'Token valide',
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
    })