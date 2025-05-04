from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout

from ..serializers.login_logout_serializers import LoginSerializer, UserSerializer



class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        
        # Génère ou récupère un token pour l'API
        token, created = Token.objects.get_or_create(user=user)
        
        # Retourne les informations utilisateur avec son token
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Supprime le token API s'il existe
        try:
            request.user.auth_token.delete()
        except (AttributeError, Token.DoesNotExist):
            pass
        
        # Déconnexion de la session
        logout(request)
        
        return Response({"detail": "Déconnexion réussie."}, status=status.HTTP_200_OK)