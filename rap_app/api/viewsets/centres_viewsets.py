from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, extend_schema_view
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from ..serializers.centres_serializers import CentreConstantsSerializer, CentreSerializer
from ...models.centres import Centre
from ..permissions import ReadWriteAdminReadStaff
from ..paginations import RapAppPagination
from ...models.logs import LogUtilisateur


@extend_schema_view(
    list=extend_schema(summary="Lister les centres", tags=["Centres"]),
    retrieve=extend_schema(summary="Récupérer un centre", tags=["Centres"]),
    create=extend_schema(summary="Créer un centre", tags=["Centres"]),
    update=extend_schema(summary="Mettre à jour un centre", tags=["Centres"]),
    partial_update=extend_schema(summary="Mettre à jour partiellement un centre", tags=["Centres"]),
    destroy=extend_schema(summary="Supprimer (logiquement) un centre", tags=["Centres"]),
)
class CentreViewSet(viewsets.ModelViewSet):
    serializer_class = CentreSerializer
    pagination_class = RapAppPagination
    permission_classes = [IsAuthenticated & ReadWriteAdminReadStaff]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['nom', 'code_postal']
    search_fields = ['nom', 'code_postal']
    ordering_fields = ['nom', 'created_at']

    def get_queryset(self):
        return Centre.objects.all().order_by("nom")


    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        centre = Centre(**serializer.validated_data)
        centre.is_active = True  # ← activation forcée
        centre.save(user=request.user)
        LogUtilisateur.log_action(centre, LogUtilisateur.ACTION_CREATE, request.user)
        return Response({
            "success": True,
            "message": "Centre créé avec succès.",
            "data": centre.to_serializable_dict()
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        LogUtilisateur.log_action(instance, LogUtilisateur.ACTION_UPDATE, request.user)
        return Response({
            "success": True,
            "message": "Centre mis à jour avec succès.",
            "data": instance.to_serializable_dict()
        })

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        LogUtilisateur.log_action(
            instance, LogUtilisateur.ACTION_UPDATE, request.user, details="Mise à jour partielle"
        )
        return Response({
            "success": True,
            "message": "Centre partiellement mis à jour.",
            "data": instance.to_serializable_dict()
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save(user=request.user)
        LogUtilisateur.log_action(instance, LogUtilisateur.ACTION_DELETE, request.user)
        return Response({
        "success": True,
        "message": "Centre désactivé avec succès."
        }, status=status.HTTP_200_OK)




class CentreConstantsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        serializer = CentreConstantsSerializer()
        return Response(serializer.data)
