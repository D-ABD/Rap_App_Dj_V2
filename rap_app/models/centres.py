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
        # Si vous ajoutez un champ statut:
        # return self.filter(statut='actif')
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
        year = year or now().year   # <-- utiliser 'year', pas 'annee'
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
            
        return self.filter(
            Q(nom__icontains=query) | 
            Q(code_postal__startswith=query)
        )


class Centre(BaseModel):
    """
    Modèle représentant un centre de formation.
    
    Ce modèle stocke les informations de base d'un centre de formation,
    notamment son nom unique et sa localisation (code postal).
    
    Attributs:
        nom (str): Nom unique du centre (max 255 caractères)
        code_postal (str, optional): Code postal à 5 chiffres du centre
        
    Propriétés:
        full_address: Adresse formatée sous forme de texte
        nb_prepa_comp_global: Nombre d'objectifs annuels associés (mise en cache)
        
    Relations:
        prepa_global: Relations OneToMany avec PrepaCompGlobal
        
    Méthodes:
        clean: Validation spécifique pour le code postal
        to_serializable_dict: Représentation JSON du centre
        invalidate_caches: Invalide les caches de propriétés
        to_csv_row: Convertit l'instance en ligne CSV
    """
    # Constantes pour éviter les valeurs magiques
    NOM_MAX_LENGTH = 255
    CODE_POSTAL_LENGTH = 5
    
    # Choix pour un éventuel statut (à ajouter si pertinent)
    STATUS_CHOICES = [
        ('actif', 'Actif'),
        ('inactif', 'Inactif'),
        ('temporaire', 'Temporaire'),
    ]

    nom = models.CharField(
        max_length=NOM_MAX_LENGTH,
        unique=True,
        verbose_name="Nom du centre",
        help_text="Nom complet du centre de formation (doit être unique)",
        db_index=True,  # Optimisation: ajout explicite d'index pour le nom
    )

    code_postal = models.CharField(
        max_length=CODE_POSTAL_LENGTH,
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
    

    # Managers
    objects = models.Manager()  # Manager par défaut
    custom = CentreManager()    # Manager personnalisé
    
    class Meta:
        verbose_name = "Centre"
        verbose_name_plural = "Centres"
        ordering = ['nom']
        indexes = [
            models.Index(fields=['nom'], name='centre_nom_idx'),
            models.Index(fields=['code_postal'], name='centre_cp_idx'),
            # Ajouter d'autres index composites si nécessaire:
        ]
        # Contraintes optionnelles
        constraints = [
            # Exemple de contrainte check
            models.CheckConstraint(
                check=~Q(nom=''), 
                name='centre_nom_not_empty'
            ),
        ]
    
    class APIInfo:
        """Informations pour la documentation API."""
        description = "Centres de formation"
        allowed_methods = ['GET', 'POST', 'PUT', 'DELETE']
        filterable_fields = ['nom', 'code_postal']
        searchable_fields = ['nom']
        ordering_fields = ['nom', 'created_at']

    def __str__(self):
        """Représentation textuelle du centre."""
        return self.nom

    def __repr__(self):
        """Représentation pour le débogage."""
        return f"<Centre {self.pk}: {self.nom}>"

    def full_address(self) -> str:
        """Retourne l'adresse complète sous forme textuelle."""
        address = self.nom
        if self.code_postal:
            address += f" ({self.code_postal})"
        return address
    from django.utils.functional import cached_property

    @cached_property
    def nb_prepa_comp_global(self):
        """
        Nombre d'objectifs annuels associés à ce centre.
        Utilisation de cached_property pour optimiser les performances.
        
        Returns:
            int: Nombre d'objectifs PrepaCompGlobal associés
        """
        from .prepacomp import PrepaCompGlobal
        return PrepaCompGlobal.objects.filter(centre=self).count()

    
    # Suppression de la propriété is_active qui masquait potentiellement
    # un champ is_active hérité de BaseModel
    
    # Si nécessaire, ajouter une propriété avec un nom différent:
    # @property
    # def is_actif_par_statut(self):
    #     """
    #     Détermine si le centre est actif selon son statut.
    #     Returns:
    #         bool: True si le centre a un statut actif, False sinon
    #     """
    #     return self.statut == 'actif' if hasattr(self, 'statut') else True

    def invalidate_caches(self):
        """
        Invalide toutes les propriétés mises en cache avec @cached_property.
        """
        for prop in ['nb_prepa_comp_global']:
            self.__dict__.pop(prop, None)


    def to_serializable_dict(self, include_related=False) -> dict:
        """
        Renvoie un dictionnaire JSON-serializable de l'objet.
        
        Args:
            include_related (bool): Si True, inclut les objets liés
            
        Returns:
            dict: Représentation sérialisable du centre
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
        
        # Fusionner avec le dictionnaire de base
        result = {**base_dict, **centre_dict}
        
        # Ajouter les objets liés si demandé
        if include_related:
            from .prepacomp import PrepaCompGlobal
            current_year = now().year  
            prepa_global = PrepaCompGlobal.objects.filter(
                centre=self, 
                annee=current_year
            ).first()
            
            if prepa_global:
                result["prepa_global"] = {
                    "id": prepa_global.pk,
                    "annee": prepa_global.annee,
                    # Ajouter d'autres champs pertinents
                }
        
        return result

    def save(self, *args, **kwargs):
        """
        Sauvegarde le centre avec journalisation améliorée.
        Préserve la compatibilité avec le code existant.
        
        Args:
            *args: Arguments positionnels pour save()
            **kwargs: Arguments nommés pour save(), y compris user
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

        # Validation métier avant sauvegarde
        self.clean()
        
        # Appel de la méthode save du BaseModel avec l'utilisateur directement
        super().save(*args, user=user, **kwargs)

        logger.debug(f"[Centre] Sauvegarde complète de #{self.pk} (user={user})")
        
        # Invalidation du cache
        self.invalidate_caches()

    def delete(self, *args, **kwargs):
        """
        Supprime le centre avec journalisation.
        
        Args:
            *args: Arguments positionnels pour delete()
            **kwargs: Arguments nommés pour delete()
            
        Returns:
            tuple: Résultat de la suppression (nombre d'objets, dict par type)
        """
        logger.warning(f"[Centre] Suppression du centre #{self.pk}: {self.nom}")
        
        # Invalidation du cache avant suppression
        self.invalidate_caches()
        
        # Suppression effective
        return super().delete(*args, **kwargs)

    def clean(self):
        """
        Validation métier spécifique pour le centre.
        
        Raises:
            ValidationError: Si les données ne sont pas valides
        """
        super().clean()
        
        # Validation du code postal
        if self.code_postal:
            if not self.code_postal.isdigit():
                raise ValidationError({"code_postal": "Le code postal doit être numérique."})
            if len(self.code_postal) != self.CODE_POSTAL_LENGTH:
                raise ValidationError({"code_postal": f"Le code postal doit contenir exactement {self.CODE_POSTAL_LENGTH} chiffres."})

    def prepa_global(self, annee=None):
        """
        Raccourci pour accéder à l'objectif annuel via PrepaCompGlobal.
        
        Args:
            annee (int, optional): Année de référence, par défaut l'année en cours
            
        Returns:
            PrepaCompGlobal: L'instance pour ce centre et cette année, ou None
        """
        from .prepacomp import PrepaCompGlobal
        annee = annee or now().year
        return PrepaCompGlobal.objects.filter(centre=self, annee=annee).first()
    
    def mark_as_inactive(self):
        """
        Marque le centre comme inactif (si un champ statut existe).
        
        Returns:
            bool: True si l'opération a réussi, False sinon
        """
        # Si vous ajoutez un champ statut:
        # self.statut = 'inactif'
        # self.save()
        # return True
        logger.warning(f"[Centre] Tentative de désactivation du centre #{self.pk}, mais pas de champ statut")
        return False
    
    def handle_related_update(self, related_object):
        """
        Gère la mise à jour des objets liés.
        À appeler lorsqu'un objet lié est modifié.
        
        Args:
            related_object: L'objet lié qui a été modifié
        """
        logger.info(f"[Centre] Objet lié mis à jour pour le centre {self.nom}: {related_object}")
        
        # Invalidation du cache
        self.invalidate_caches()
    
    @classmethod
    def get_centres_by_region(cls, region=None):
        """
        Méthode de classe pour récupérer les centres par région.
        Exemple de méthode utilitaire à implémenter si vous ajoutez un champ region.
        
        Args:
            region (str, optional): Région à filtrer, tous si None
            
        Returns:
            QuerySet: Les centres de la région spécifiée ou tous
        """
        queryset = cls.objects.all()
        
        # Si vous ajoutez un champ region:
        # if region:
        #     queryset = queryset.filter(region=region)
        
        return queryset.order_by('nom')
    
    @classmethod
    def get_centres_with_stats(cls):
        """
        Récupère tous les centres avec des statistiques calculées.
        Utilise des annotations pour optimiser les performances.
        
        Returns:
            QuerySet: Centres avec statistiques annotées
        """
        # Utilisation du manager personnalisé
        return cls.custom.with_prepa_counts().order_by('nom')
    
    @classmethod
    def get_csv_fields(cls):
        """
        Définit les champs à inclure dans un export CSV.
        
        Returns:
            list: Liste des noms de champs
        """
        return ['id', 'nom', 'code_postal', 'created_at', 'updated_at']
    
    @classmethod
    def get_csv_headers(cls):
        """
        Définit les en-têtes pour un export CSV.
        
        Returns:
            list: Liste des en-têtes de colonnes
        """
        return [
            'ID', 
            'Nom du centre', 
            'Code postal', 
            'Date de création', 
            'Date de mise à jour'
        ]
    
    def to_csv_row(self):
        """
        Convertit l'instance en ligne CSV.
        
        Returns:
            list: Valeurs pour une ligne CSV
        """
        return [
            self.pk,
            self.nom,
            self.code_postal or '',
            self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else '',
            self.updated_at.strftime('%Y-%m-%d %H:%M') if self.updated_at else ''
        ]