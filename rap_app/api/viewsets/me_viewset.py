from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..serializers.user_profil_serializers import UserProfileSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    """
    ✅ Retourne les infos du user connecté.
    """
    user = request.user
    serializer = UserProfileSerializer(user, context={'request': request})
    return Response(serializer.data)
