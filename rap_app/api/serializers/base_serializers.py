from rest_framework import serializers

class EmptySerializer(serializers.Serializer):
    """Serializer générique vide, utilisé pour les vues de statistiques ou d'export."""
    pass
