from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class LogUtilisateur(models.Model):
    """Log générique pour tracer les actions des utilisateurs dans l'app."""

    utilisateur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Utilisateur"
    )
    modele = models.CharField(
        max_length=100,
        verbose_name="Modèle concerné"
    )
    object_id = models.PositiveIntegerField(
        verbose_name="ID de l'objet"
    )
    action = models.CharField(
        max_length=255,
        verbose_name="Action"
    )
    details = models.TextField(
        blank=True,
        null=True,
        verbose_name="Détails complémentaires"
    )
    date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de l'action"
    )

    class Meta:
        verbose_name = "Log utilisateur"
        verbose_name_plural = "Logs utilisateurs"
        ordering = ['-date']

    def __str__(self):
        return f"{self.utilisateur} - {self.action} - {self.modele}({self.object_id})"
