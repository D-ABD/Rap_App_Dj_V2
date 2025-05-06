from django.db import models
from .base import BaseModel  # Assure-toi que BaseModel est bien importé

class LogUtilisateur(BaseModel):
    """
    Log simplifié pour tracer les actions des utilisateurs dans l'application.
    Hérite de BaseModel pour les dates et les utilisateurs.
    """

    action = models.CharField(
        max_length=255,
        verbose_name="Action",
        help_text="Type d'action (création, modification, suppression...)"
    )

    details = models.TextField(
        blank=True,
        null=True,
        verbose_name="Détails",
        help_text="Informations supplémentaires sur l'action"
    )

    class Meta:
        verbose_name = "Log utilisateur"
        verbose_name_plural = "Logs utilisateurs"
        ordering = ['-created_at']  # Utilisation de created_at pour l'ordre

    def __str__(self):
        return f"{self.action} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"
