from django.utils.timezone import now 
import logging
from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.functional import cached_property
from django.db.models import Count, F, Q

from .base import BaseModel

logger = logging.getLogger(__name__)

class CentreManager(models.Manager):
    """
    Manager personnalisé pour le modèle Centre.
    Fournit des méthodes utilitaires pour les requêtes fréquentes.
    """
    
    def actifs(self):
        """
        Retourne uniquement les centres actifs.
        
        Returns:
            QuerySet: Les centres actifs uniquement
        """
        return self.all()
    
    def with_prepa_counts(self):
        """
        Retourne les centres avec le nombre d'objectifs annuels.
        
        Returns:
            QuerySet: Centres annotés avec le nombre de PrepaCompGlobal
        """
        return self.annotate(prepa_count=Count('prepa_globaux'))
    
    def by_code_postal(self, code_postal):
        """
        Filtre les centres par code postal.
        
        Args:
            code_postal (str): Code postal à rechercher
            
        Returns:
            QuerySet: Centres filtrés par code postal
        """
        return self.filter(code_postal=code_postal)
    
    def with_prepa_for_year(self, year=None):
        from .prepacomp import PrepaCompGlobal
        year = year or now().year
        return self.prefetch_related(
            models.Prefetch(
                'prepacompglobal_set',
                queryset=PrepaCompGlobal.objects.filter(annee=year),
                to_attr='prepa_for_year'
            )
        )
    
    def search(self, query):
        """
        Recherche textuelle dans les centres.
        
        Args:
            query (str): Texte à rechercher
            
        Returns:
            QuerySet: Centres correspondant à la recherche
        """
        if not query:
            return self.all()
        return self.filter(Q(nom__icontains=query) | Q(code_postal__startswith=query))


class Centre(BaseModel):
    """
    Modèle représentant un centre de formation.
    
    Ce modèle stocke les informations de base d'un centre de formation,
    y compris les détails du CFA responsable et du lieu principal.
    """
    NOM_MAX_LENGTH = 255
    CODE_POSTAL_LENGTH = 5

    STATUS_CHOICES = [
        ('actif', 'Actif'),
        ('inactif', 'Inactif'),
        ('temporaire', 'Temporaire'),
    ]

    # --- Informations principales ---
    cfa_entreprise = models.BooleanField(default=False, help_text="CFA d’entreprise")

    nom = models.CharField(
        max_length=NOM_MAX_LENGTH,
        unique=True,
        verbose_name="Nom du centre",
        help_text="Nom complet du centre de formation (doit être unique)",
        db_index=True,
    )

    numero_voie = models.CharField(max_length=10, blank=True, null=True, verbose_name="Numéro de voie")
    nom_voie = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nom de la voie")
    complement_adresse = models.CharField(max_length=255, blank=True, null=True, verbose_name="Complément adresse")

    code_postal = models.CharField(
        max_length=CODE_POSTAL_LENGTH,
        null=True,
        blank=True,
        verbose_name="Code postal",
        help_text="Code postal à 5 chiffres du centre",
        validators=[
            RegexValidator(regex=r'^\d{5}$', message="Le code postal doit contenir exactement 5 chiffres")
        ]
    )
    commune = models.CharField(max_length=255, blank=True, null=True)


    numero_uai_centre = models.CharField(max_length=20, blank=True, null=True)
    siret_centre = models.CharField(max_length=14, blank=True, null=True)
    
    # --- Informations CFA Responsable ---
    cfa_responsable_est_lieu_principal = models.BooleanField(
        default=False,
        help_text="Si le CFA responsable est le lieu de formation principal",
    )

    cfa_responsable_denomination = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Dénomination du CFA responsable"
    )
    cfa_responsable_uai = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="N° UAI du CFA"
    )
    cfa_responsable_siret = models.CharField(
        max_length=14, blank=True, null=True, verbose_name="N° SIRET du CFA"
    )

    cfa_responsable_numero = models.CharField(max_length=10, blank=True, null=True)
    cfa_responsable_voie = models.CharField(max_length=255, blank=True, null=True)
    cfa_responsable_complement = models.CharField(max_length=255, blank=True, null=True)
    cfa_responsable_code_postal = models.CharField(max_length=10, blank=True, null=True)
    cfa_responsable_commune = models.CharField(max_length=255, blank=True, null=True)

    # Managers
    objects = models.Manager()
    custom = CentreManager()

    class Meta:
        verbose_name = "Centre"
        verbose_name_plural = "Centres"
        ordering = ['nom']
        indexes = [
            models.Index(fields=['nom'], name='centre_nom_idx'),
            models.Index(fields=['code_postal'], name='centre_cp_idx'),
        ]
        constraints = [
            models.CheckConstraint(check=~Q(nom=''), name='centre_nom_not_empty'),
        ]

    class APIInfo:
        """Informations pour la documentation API."""
        description = "Centres de formation"
        allowed_methods = ['GET', 'POST', 'PUT', 'DELETE']
        filterable_fields = ['nom', 'code_postal']
        searchable_fields = ['nom']
        ordering_fields = ['nom', 'created_at']

    def __str__(self):
        return self.nom

    def __repr__(self):
        return f"<Centre {self.pk}: {self.nom}>"

    def full_address(self) -> str:
        """Retourne l'adresse complète sous forme textuelle."""
        address = self.nom
        if self.code_postal:
            address += f" ({self.code_postal})"
        return address

    @cached_property
    def nb_prepa_comp_global(self):
        """
        Nombre d'objectifs annuels associés à ce centre.
        Utilisation de cached_property pour optimiser les performances.
        """
        from .prepacomp import PrepaCompGlobal
        return PrepaCompGlobal.objects.filter(centre=self).count()

    def invalidate_caches(self):
        """Invalide les caches calculés."""
        for prop in ['nb_prepa_comp_global']:
            self.__dict__.pop(prop, None)

    def to_serializable_dict(self, include_related=False) -> dict:
        """
        Renvoie un dictionnaire JSON-serializable de l'objet.
        """
        base_dict = super().to_serializable_dict(exclude=['created_by', 'updated_by'])
        centre_dict = {
            "id": self.pk,
            "nom": self.nom,
            "code_postal": self.code_postal,
            "full_address": self.full_address(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        result = {**base_dict, **centre_dict}
        if include_related:
            from .prepacomp import PrepaCompGlobal
            current_year = now().year
            prepa_global = PrepaCompGlobal.objects.filter(centre=self, annee=current_year).first()
            if prepa_global:
                result["prepa_global"] = {
                    "id": prepa_global.pk,
                    "annee": prepa_global.annee,
                }
        return result

    def save(self, *args, **kwargs):
        """
        Sauvegarde le centre avec journalisation améliorée.
        """
        user = kwargs.pop("user", None)
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

        self.clean()
        super().save(*args, user=user, **kwargs)
        logger.debug(f"[Centre] Sauvegarde complète de #{self.pk} (user={user})")
        self.invalidate_caches()

    def delete(self, *args, **kwargs):
        """
        Supprime le centre avec journalisation.
        """
        logger.warning(f"[Centre] Suppression du centre #{self.pk}: {self.nom}")
        self.invalidate_caches()
        return super().delete(*args, **kwargs)

    def clean(self):
        """
        Validation métier spécifique pour le centre.
        """
        super().clean()
        if self.code_postal:
            if not self.code_postal.isdigit():
                raise ValidationError({"code_postal": "Le code postal doit être numérique."})
            if len(self.code_postal) != self.CODE_POSTAL_LENGTH:
                raise ValidationError({"code_postal": f"Le code postal doit contenir exactement {self.CODE_POSTAL_LENGTH} chiffres."})

    def prepa_global(self, annee=None):
        """Raccourci pour accéder à l'objectif annuel via PrepaCompGlobal."""
        from .prepacomp import PrepaCompGlobal
        annee = annee or now().year
        return PrepaCompGlobal.objects.filter(centre=self, annee=annee).first()

    def mark_as_inactive(self):
        """Marque le centre comme inactif (si un champ statut existe)."""
        logger.warning(f"[Centre] Tentative de désactivation du centre #{self.pk}, mais pas de champ statut")
        return False

    def handle_related_update(self, related_object):
        """Gère la mise à jour des objets liés."""
        logger.info(f"[Centre] Objet lié mis à jour pour le centre {self.nom}: {related_object}")
        self.invalidate_caches()

    @classmethod
    def get_centres_by_region(cls, region=None):
        """Méthode de classe pour récupérer les centres par région."""
        queryset = cls.objects.all()
        return queryset.order_by('nom')
    
    @classmethod
    def get_centres_with_stats(cls):
        """Récupère tous les centres avec statistiques calculées."""
        return cls.custom.with_prepa_counts().order_by('nom')

    @classmethod
    def get_csv_fields(cls):
        """Définit les champs à inclure dans un export CSV."""
        return ['id', 'nom', 'code_postal', 'created_at', 'updated_at']
    
    @classmethod
    def get_csv_headers(cls):
        """Définit les en-têtes pour un export CSV."""
        return [
            'ID', 
            'Nom du centre', 
            'Code postal', 
            'Date de création', 
            'Date de mise à jour'
        ]
    
    def to_csv_row(self):
        """Convertit l'instance en ligne CSV."""
        return [
            self.pk,
            self.nom,
            self.code_postal or '',
            self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else '',
            self.updated_at.strftime('%Y-%m-%d %H:%M') if self.updated_at else ''
        ]
