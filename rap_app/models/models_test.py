from django.db import models
from .base import BaseModel  # Assure-toi que le chemin est correct

class DummyModel(BaseModel):
    """
    Modèle factice utilisé uniquement pour les tests du modèle de base.
    """
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"DummyModel #{self.pk}"


