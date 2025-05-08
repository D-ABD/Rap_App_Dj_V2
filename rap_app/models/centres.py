from datetime import timezone
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
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

    def __repr__(self):
        return f"<Centre {self.pk}: {self.nom}>"

    def get_absolute_url(self):
        return reverse('centre-detail', kwargs={'pk': self.pk})

    def full_address(self) -> str:
        """Retourne l'adresse complète sous forme textuelle."""
        address = self.nom
        if self.code_postal:
            address += f" ({self.code_postal})"
        return address

    def to_serializable_dict(self) -> dict:
        """Renvoie un dictionnaire JSON-serializable de l'objet."""
        return {
            "id": self.pk,
            "nom": self.nom,
            "code_postal": self.code_postal,
            "full_address": self.full_address(),
            "url": self.get_absolute_url(),
        }

    def save(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        if user:
            self._user = user  # transmis au BaseModel

        is_new = self.pk is None

        if is_new:
            logger.info(f"[Centre] Création: {self.nom}")
        else:
            try:
                old = Centre.objects.get(pk=self.pk)
                changes = []
                if old.nom != self.nom:
                    changes.append(f"nom: '{old.nom}' → '{self.nom}'")
                if old.code_postal != self.code_postal:
                    changes.append(f"code_postal: '{old.code_postal}' → '{self.code_postal}'")
                if changes:
                    logger.info(f"[Centre] Modif #{self.pk}: {', '.join(changes)}")
            except Centre.DoesNotExist:
                logger.warning(f"[Centre] Ancienne instance introuvable pour {self.pk}")

        super().save(*args, **kwargs)

        logger.debug(f"[Centre] Sauvegarde complète de #{self.pk} (user={getattr(self, '_user', None)})")

    def clean(self):
        """Validation métier spécifique pour le code postal."""
        super().clean()
        if self.code_postal and not self.code_postal.isdigit():
            raise ValidationError("Le code postal doit être numérique.")

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
@receiver(post_save, sender=Centre)
def log_centre_saved(sender, instance, created, **kwargs):
    if created:
        logger.info(f"[Signal] Nouveau centre créé : {instance.nom}")
    else:
        logger.info(f"[Signal] Centre mis à jour : {instance.nom}")