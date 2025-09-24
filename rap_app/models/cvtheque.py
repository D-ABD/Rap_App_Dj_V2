# models.py
import os
import logging
from django.db import models
from django.db import transaction
from django.core.validators import FileExtensionValidator
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.exceptions import ValidationError

# Configuration du logger
logger = logging.getLogger(__name__)

def cv_upload_path(instance, filename):
    """Chemin de stockage des CV : cvtheque/candidat_<id>/<filename>"""
    base_name, ext = os.path.splitext(filename)
    safe_name = f"cv_{instance.candidat.id}_{base_name[:50]}{ext}".replace(' ', '_')
    path = f'cvtheque/candidat_{instance.candidat.id}/{safe_name}'
    logger.debug(f"Génération du chemin de stockage : {path}")
    return path

class CVTheque(models.Model):
    """Modèle pour la gestion centralisée des CV des candidats"""
    
    # Types de documents acceptés
    DOCUMENT_TYPES = [
        ('CV', 'Curriculum Vitae'),
        ('LM', 'Lettre de motivation'),
        ('DIPLOME', 'Diplôme/Certificat'),
        ('AUTRE', 'Autre document'),
    ]

    candidat = models.ForeignKey(
        'Candidat',
        on_delete=models.CASCADE,
        related_name='cvs',
        verbose_name=_("Candidat")
    )

    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPES,
        default='CV',
        verbose_name=_("Type de document")
    )

    fichier = models.FileField(
        upload_to=cv_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])],
        verbose_name=_("Fichier"),
        help_text=_("Formats acceptés : PDF, DOC, DOCX (max. 5Mo)")
    )

    titre = models.CharField(
        max_length=255,
        verbose_name=_("Titre du document"),
        help_text=_("Ex: CV 2023, Lettre de motivation pour poste X")
    )

    date_depot = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de dépôt")
    )

    est_public = models.BooleanField(
        default=False,
        verbose_name=_("Visible par les recruteurs"),
        help_text=_("Ce document peut-il être visible par les recruteurs ?")
    )

    mots_cles = models.TextField(
        blank=True,
        verbose_name=_("Mots-clés"),
        help_text=_("Mots-clés pour la recherche (séparés par des virgules)")
    )

    class Meta:
        verbose_name = _("CVthèque")
        verbose_name_plural = _("CVthèque")
        ordering = ['-date_depot']
        constraints = [
            models.UniqueConstraint(
                fields=['candidat', 'titre'],
                name='unique_cv_per_candidat'
            )
        ]

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.candidat} ({self.date_depot.date()})"

    @property
    def extension(self):
        """Retourne l'extension du fichier"""
        ext = os.path.splitext(self.fichier.name)[1][1:].lower()
        logger.debug(f"Extension détectée pour le document {self.pk}: {ext}")
        return ext

    @property
    def taille(self):
        """Retourne la taille formatée"""
        if not self.fichier:
            logger.warning(f"Document {self.pk} sans fichier attaché")
            return "0 KB"
            
        try:
            size = self.fichier.size
            if size < 1024 * 1024:  # Moins de 1MB
                return f"{size / 1024:.1f} KB"
            return f"{size / (1024 * 1024):.1f} MB"
        except Exception as e:
            logger.error(f"Erreur lors du calcul de la taille pour le document {self.pk}: {str(e)}")
            return "Taille inconnue"

    def get_absolute_url(self):
        url = reverse('cvtheque:detail', kwargs={'pk': self.pk})
        logger.debug(f"URL absolue générée pour le document {self.pk}: {url}")
        return url

    def clean(self):
        """Validation et nettoyage des données"""
        super().clean()
        logger.info(f"Début du nettoyage pour le document {self.pk or 'nouveau'}")
        
        # Validation du titre
        if not self.titre or not self.titre.strip():
            logger.error("Tentative de sauvegarde sans titre")
            raise ValidationError({"titre": "Le titre du document est obligatoire."})
        
        # Validation de la taille du fichier
        if self.fichier and hasattr(self.fichier, 'size'):
            max_size = 5 * 1024 * 1024  # 5MB
            if self.fichier.size > max_size:
                logger.warning(f"Fichier trop volumineux ({self.fichier.size} bytes) pour le document {self.pk}")
                raise ValidationError({
                    "fichier": "Le fichier ne doit pas dépasser 5 Mo."
                })
        
        logger.info(f"Nettoyage terminé pour le document {self.pk or 'nouveau'}")

    @transaction.atomic
    def save(self, *args, **kwargs):
        """
        Sauvegarde du document avec journalisation
        """
        is_new = self.pk is None
        
        try:
            logger.info(f"Début de la sauvegarde du document {self.pk or 'nouveau'}")
            super().save(*args, **kwargs)
            
            if is_new:
                logger.info(f"Nouveau document créé: {self} (ID: {self.pk})")
                # Exemple d'intégration avec un système d'historique
                try:
                    from ..signals import document_created
                    document_created.send(sender=self.__class__, instance=self)
                except ImportError:
                    pass
            else:
                logger.debug(f"Document mis à jour: {self.pk}")
                
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du document: {str(e)}", exc_info=True)
            raise
            
        logger.info(f"Sauvegarde terminée pour le document {self.pk}")

    def delete(self, *args, **kwargs):
        """
        Suppression du document avec journalisation
        """
        try:
            logger.info(f"Début de la suppression du document {self.pk}")
            file_path = self.fichier.path if self.fichier else None
            
            super().delete(*args, **kwargs)
            
            logger.info(f"Document supprimé: {self.pk}")
            
            # Nettoyage optionnel du fichier physique
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.debug(f"Fichier physique supprimé: {file_path}")
                except OSError as e:
                    logger.error(f"Erreur lors de la suppression du fichier {file_path}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du document {self.pk}: {str(e)}", exc_info=True)
            raise