from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema

from ...utils.filters import AtelierTREFilter

from ...models.atelier_tre import AtelierTRE, ParticipationAtelierTRE
from ..serializers.atelier_tre_serializers import (
    AtelierTRESerializer,
    AtelierTREListSerializer,
    AtelierTRECreateUpdateSerializer,
    AtelierTREMetaSerializer,
    ParticipationAtelierTRESerializer,
    ParticipationAtelierTRECreateUpdateSerializer
)
from ..permissions import IsStaffOrAbove
from ..paginations import RapAppPagination


class AtelierTREViewSet(viewsets.ModelViewSet):
    queryset = AtelierTRE.objects.all().prefetch_related("participationateliertre_set__candidat")
    permission_classes = [IsStaffOrAbove]
    pagination_class = RapAppPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = AtelierTREFilter

    def get_serializer_class(self):
        if self.action == "list":
            return AtelierTREListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return AtelierTRECreateUpdateSerializer
        return AtelierTRESerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @extend_schema(responses=AtelierTREMetaSerializer)
    @action(detail=False, methods=["get"], url_path="meta", url_name="meta")
    def meta(self, request):
        return Response(AtelierTREMetaSerializer().data)

class ParticipationAtelierTREViewSet(viewsets.ModelViewSet):
    queryset = ParticipationAtelierTRE.objects.select_related("candidat", "ateliertre")
    permission_classes = [IsStaffOrAbove]
    pagination_class = RapAppPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["ateliertre", "present", "candidat"]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ParticipationAtelierTRECreateUpdateSerializer
        return ParticipationAtelierTRESerializer
