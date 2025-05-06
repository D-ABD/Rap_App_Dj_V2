from datetime import timezone
import logging
from django.db import models
from django.core.validators import RegexValidator
from django.urls import reverse
from .base import BaseModel

logger = logging.getLogger(__name__)

class Centre(BaseModel):
    """
    Modèle représentant un centre de formation.

    Champs :
    - nom : Nom unique du centre.
    - code_postal : Code postal à 5 chiffres (optionnel).

    Méthodes :
    - __str__ : Nom du centre.
    - get_absolute_url : URL vers le détail.
    - full_address : Adresse lisible.
    - prepa_global : Récupère les objectifs annuels via PrepaCompGlobal.
    """

    nom = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Nom du centre",
        help_text="Nom complet du centre de formation (doit être unique)"
    )

    code_postal = models.CharField(
        max_length=5,
        null=True,
        blank=True,
        verbose_name="Code postal",
        help_text="Code postal à 5 chiffres du centre",
        validators=[
            RegexValidator(
                regex=r'^\d{5}$',
                message="Le code postal doit contenir exactement 5 chiffres"
            )
        ]
    )

    def __str__(self):
        return self.nom

    def get_absolute_url(self):
        return reverse('centre-detail', kwargs={'pk': self.pk})

    def full_address(self):
        address = self.nom
        if self.code_postal:
            address += f" ({self.code_postal})"
        return address

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        if is_new:
            logger.info(f"Création d'un nouveau centre: {self.nom}")
        else:
            try:
                old = Centre.objects.get(pk=self.pk)
                changes = []
                if old.nom != self.nom:
                    changes.append(f"nom: '{old.nom}' → '{self.nom}'")
                if old.code_postal != self.code_postal:
                    changes.append(f"code_postal: '{old.code_postal}' → '{self.code_postal}'")
                if changes:
                    logger.info(f"Modification du centre #{self.pk}: {', '.join(changes)}")
            except Centre.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        if is_new:
            logger.info(f"Centre #{self.pk} '{self.nom}' créé avec succès")

    def prepa_global(self, annee=None):
        """
        Raccourci pour accéder à l'objectif annuel via PrepaCompGlobal.
        """
        from .prepacomp import PrepaCompGlobal
        annee = annee or timezone.now().year
        return PrepaCompGlobal.objects.filter(centre=self, annee=annee).first()

    class Meta:
        verbose_name = "Centre"
        verbose_name_plural = "Centres"
        ordering = ['nom']
        indexes = [
            models.Index(fields=['nom']),
            models.Index(fields=['code_postal']),
        ]
