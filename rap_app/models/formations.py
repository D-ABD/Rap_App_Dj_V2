import datetime
import logging
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import F, Q, Sum, Count, Case, When, Value, ExpressionWrapper, FloatField
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property


from .base import BaseModel
from .partenaires import Partenaire
from .centres import Centre
from .types_offre import TypeOffre
from .statut import Statut, get_default_color

logger = logging.getLogger("application.formation")

# ----------------------------------------------------
# Signaux déplacés dans un fichier signals/
# ----------------------------------------------------


class FormationManager(models.Manager):
    """
    Manager personnalisé pour le modèle Formation.
    Fournit des méthodes utilitaires pour filtrer et trier les formations.
    
    Utilisé dans les serializers pour:
    - Filtrer les formations selon leur état (active, à venir, terminée)
    - Trier les formations selon différents critères
    - Identifier les formations avec des places disponibles
    """

    def formations_actives(self):
        """
        Retourne uniquement les formations actives actuellement.
        
        Returns:
            QuerySet: Formations dont la date de début est passée et la date de fin est future
        """
        today = timezone.now().date()
        return self.filter(start_date__lte=today, end_date__gte=today)

    def formations_a_venir(self):
        """
        Retourne uniquement les formations qui n'ont pas encore commencé.
        
        Returns:
            QuerySet: Formations dont la date de début est dans le futur
        """
        return self.filter(start_date__gt=timezone.now().date())

    def formations_terminees(self):
        """
        Retourne uniquement les formations déjà terminées.
        
        Returns:
            QuerySet: Formations dont la date de fin est passée
        """
        return self.filter(end_date__lt=timezone.now().date())

    def formations_a_recruter(self):
        """
        Retourne les formations qui ont encore des places disponibles.
        Utilisée pour les pages de recrutement et les filtres de recherche.
        
        Returns:
            QuerySet: Formations avec des places disponibles
        """
        return self.annotate(
            total_places=models.F('prevus_crif') + models.F('prevus_mp'),
            total_inscrits=models.F('inscrits_crif') + models.F('inscrits_mp')
        ).filter(total_places__gt=models.F('total_inscrits'))

    def formations_toutes(self):
        """
        Retourne toutes les formations sans filtre.
        
        Returns:
            QuerySet: Toutes les formations
        """
        return self.all()

    def trier_par(self, champ_tri):
        """
        Trie les formations selon un champ donné, si autorisé.
        Utilisé pour les tris dans l'interface utilisateur.
        
        Args:
            champ_tri (str): Nom du champ à utiliser pour le tri, peut inclure un '-' pour tri descendant
            
        Returns:
            QuerySet: Formations triées selon le champ demandé, ou sans tri si le champ n'est pas autorisé
        """
        champs_autorises = [
            "centre", "-centre", "statut", "-statut",
            "type_offre", "-type_offre", "start_date", "-start_date",
            "end_date", "-end_date", "nom", "-nom",
            "total_places", "-total_places", "total_inscrits", "-total_inscrits",
            "taux_saturation", "-taux_saturation"
        ]
        
        if champ_tri in ["total_places", "-total_places", "total_inscrits", "-total_inscrits", 
                         "taux_saturation", "-taux_saturation"]:
            # Pour les champs calculés, nous devons annoter le queryset
            queryset = self.get_queryset().annotate(
                total_places=models.F('prevus_crif') + models.F('prevus_mp'),
                total_inscrits=models.F('inscrits_crif') + models.F('inscrits_mp'),
                taux_saturation=Case(
                    When(total_places__gt=0, 
                         then=ExpressionWrapper(
                            100.0 * models.F('total_inscrits') / models.F('total_places'),
                            output_field=FloatField()
                         )),
                    default=Value(0.0),
                    output_field=FloatField()
                )
            )
            return queryset.order_by(champ_tri)
        
        return self.get_queryset().order_by(champ_tri) if champ_tri in champs_autorises else self.get_queryset()
        
    def recherche(self, texte=None, type_offre=None, centre=None, statut=None, 
                 date_debut=None, date_fin=None, places_disponibles=False):
        """
        Recherche avancée de formations selon différents critères.
        
        Args:
            texte (str, optional): Texte à rechercher dans le nom ou les numéros
            type_offre (int, optional): ID du type d'offre
            centre (int, optional): ID du centre
            statut (int, optional): ID du statut
            date_debut (date, optional): Date de début minimum
            date_fin (date, optional): Date de fin maximum
            places_disponibles (bool, optional): Si True, seulement les formations avec places
            
        Returns:
            QuerySet: Formations correspondant aux critères
        """
        queryset = self.get_queryset()
        
        # Filtres textuels
        if texte:
            queryset = queryset.filter(
                Q(nom__icontains=texte) | 
                Q(num_kairos__icontains=texte) | 
                Q(num_offre__icontains=texte) |
                Q(num_produit__icontains=texte)
            )
        
        # Filtres sur les relations
        if type_offre:
            queryset = queryset.filter(type_offre_id=type_offre)
        if centre:
            queryset = queryset.filter(centre_id=centre)
        if statut:
            queryset = queryset.filter(statut_id=statut)
        
        # Filtres sur les dates
        if date_debut:
            queryset = queryset.filter(start_date__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(end_date__lte=date_fin)
        
        # Filtre sur les places disponibles
        if places_disponibles:
            queryset = queryset.annotate(
                total_places=models.F('prevus_crif') + models.F('prevus_mp'),
                total_inscrits=models.F('inscrits_crif') + models.F('inscrits_mp')
            ).filter(total_places__gt=models.F('total_inscrits'))
        
        return queryset

    def get_formations_with_metrics(self):
        """
        Récupère les formations avec les métriques annotées pour optimiser les performances.
        
        Returns:
            QuerySet: Formations avec métriques pré-calculées
        """
        return self.annotate(
            total_places=models.F('prevus_crif') + models.F('prevus_mp'),
            total_inscrits=models.F('inscrits_crif') + models.F('inscrits_mp'),
            places_disponibles=models.ExpressionWrapper(
                models.F('total_places') - models.F('total_inscrits'),
                output_field=models.IntegerField()
            ),
            taux_saturation=Case(
                When(total_places__gt=0, 
                    then=ExpressionWrapper(
                        100.0 * models.F('total_inscrits') / models.F('total_places'),
                        output_field=models.FloatField()
                    )),
                default=Value(0.0),
                output_field=models.FloatField()
            )
        )

    def increment_attendees(self, formation_id, count=1, user=None, crif=True):
        """
        Incrémente le nombre d'inscrits de façon thread-safe.
        
        Args:
            formation_id (int): ID de la formation
            count (int): Nombre d'inscrits à ajouter
            user (User, optional): Utilisateur effectuant l'action
            crif (bool): Si True, incrémente les inscrits CRIF, sinon MP
            
        Returns:
            Formation: Instance mise à jour
        """
        with transaction.atomic():
            formation = self.select_for_update().get(pk=formation_id)
            
            field = 'inscrits_crif' if crif else 'inscrits_mp'
            old_val = getattr(formation, field)
            setattr(formation, field, old_val + count)
            
            formation.save(update_fields=[field], user=user)
            return formation


class Formation(BaseModel):
    """
    📚 Modèle représentant une formation.
    
    Ce modèle stocke toutes les informations relatives à une formation:
    - Informations générales (nom, centre, type, statut)
    - Dates et identifiants administratifs
    - Gestion des places et inscriptions
    - Statistiques et suivi
    
    Attributs:
        nom (str): Nom de la formation
        centre (Centre): Centre où se déroule la formation
        type_offre (TypeOffre): Type d'offre de formation
        statut (Statut): Statut actuel de la formation
        start_date (date): Date de début
        end_date (date): Date de fin
        prevus_crif (int): Places prévues CRIF
        prevus_mp (int): Places prévues MP
        inscrits_crif (int): Inscrits CRIF
        inscrits_mp (int): Inscrits MP
        
    Propriétés:
        total_places (int): Somme des places CRIF et MP
        total_inscrits (int): Somme des inscrits CRIF et MP
        places_disponibles (int): Places restantes disponibles
        taux_saturation (float): Pourcentage d'occupation des places
        
    Méthodes:
        add_commentaire: Ajoute un commentaire à la formation
        add_document: Ajoute un document à la formation
        add_evenement: Ajoute un événement à la formation
    """
    
    # Constantes pour les limites de champs
    NOM_MAX_LENGTH = 255
    NUM_MAX_LENGTH = 50
    ASSISTANTE_MAX_LENGTH = 255
    
    # Champs statistiques calculés automatiquement
    FIELDS_CALCULATED = ['nombre_candidats', 'nombre_entretiens', 'nombre_evenements']
    
    # Champs à journaliser dans l'historique
    FIELDS_TO_TRACK = [
        'nom', 'centre', 'type_offre', 'statut', 'start_date', 'end_date',
        'num_kairos', 'num_offre', 'num_produit', 'prevus_crif', 'prevus_mp',
        'inscrits_crif', 'inscrits_mp', 'assistante', 'cap', 'convocation_envoie',
        'entree_formation', 'nombre_candidats', 'nombre_entretiens', 'dernier_commentaire'
    ]

    # Informations générales
    nom = models.CharField(
        max_length=NOM_MAX_LENGTH, 
        verbose_name=_("Nom de la formation"),
        help_text=_("Intitulé complet de la formation")
    )
    
    centre = models.ForeignKey(
        Centre, 
        on_delete=models.CASCADE, 
        related_name='formations', 
        verbose_name=_("Centre de formation"),
        help_text=_("Centre où se déroule la formation")
    )
    
    type_offre = models.ForeignKey(
        TypeOffre, 
        on_delete=models.CASCADE, 
        related_name="formations", 
        verbose_name=_("Type d'offre"),
        help_text=_("Catégorie d'offre de formation")
    )
    
    statut = models.ForeignKey(
        Statut, 
        on_delete=models.CASCADE, 
        related_name="formations", 
        verbose_name=_("Statut de la formation"),
        help_text=_("État actuel de la formation")
    )

    # Dates et identifiants
    start_date = models.DateField(
        null=True, 
        blank=True, 
        verbose_name=_("Date de début"),
        help_text=_("Date de début de la formation")
    )
    
    end_date = models.DateField(
        null=True, 
        blank=True, 
        verbose_name=_("Date de fin"),
        help_text=_("Date de fin de la formation")
    )
    
    num_kairos = models.CharField(
        max_length=NUM_MAX_LENGTH, 
        null=True, 
        blank=True, 
        verbose_name=_("Numéro Kairos"),
        help_text=_("Identifiant Kairos de la formation")
    )
    
    num_offre = models.CharField(
        max_length=NUM_MAX_LENGTH, 
        null=True, 
        blank=True, 
        verbose_name=_("Numéro de l'offre"),
        help_text=_("Identifiant de l'offre")
    )
    
    num_produit = models.CharField(
        max_length=NUM_MAX_LENGTH, 
        null=True, 
        blank=True, 
        verbose_name=_("Numéro du produit"),
        help_text=_("Identifiant du produit de formation")
    )

    # Gestion des places et inscriptions
    prevus_crif = models.PositiveIntegerField(
        default=0, 
        verbose_name=_("Places prévues CRIF"),
        help_text=_("Nombre de places disponibles CRIF")
    )
    
    prevus_mp = models.PositiveIntegerField(
        default=0, 
        verbose_name=_("Places prévues MP"),
        help_text=_("Nombre de places disponibles MP")
    )
    
    inscrits_crif = models.PositiveIntegerField(
        default=0, 
        verbose_name=_("Inscrits CRIF"),
        help_text=_("Nombre d'inscrits CRIF")
    )
    
    inscrits_mp = models.PositiveIntegerField(
        default=0, 
        verbose_name=_("Inscrits MP"),
        help_text=_("Nombre d'inscrits MP")
    )

    saturation = models.FloatField(
        null=True, 
        blank=True, 
        verbose_name=_("Niveau de saturation moyen"),
        help_text=_("Pourcentage moyen de saturation basé sur les commentaires")
    )

    # Informations supplémentaires
    assistante = models.CharField(
        max_length=ASSISTANTE_MAX_LENGTH, 
        null=True, 
        blank=True, 
        verbose_name=_("Assistante"),
        help_text=_("Nom de l'assistante responsable")
    )
    
    cap = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        verbose_name=_("Capacité maximale"),
        help_text=_("Capacité maximale d'accueil")
    )
    
    convocation_envoie = models.BooleanField(
        default=False, 
        verbose_name=_("Convocation envoyée"),
        help_text=_("Indique si les convocations ont été envoyées")
    )
    
    entree_formation = models.PositiveIntegerField(
        default=0, 
        verbose_name=_("Entrées en formation"),
        help_text=_("Nombre de personnes entrées en formation")
    )

    # Statistiques de recrutement
    nombre_candidats = models.PositiveIntegerField(
        default=0, 
        verbose_name=_("Nombre de candidats"),
        help_text=_("Nombre total de candidats pour cette formation")
    )
    
    nombre_entretiens = models.PositiveIntegerField(
        default=0, 
        verbose_name=_("Nombre d'entretiens"),
        help_text=_("Nombre d'entretiens réalisés")
    )
    
    nombre_evenements = models.PositiveIntegerField(
        default=0, 
        verbose_name=_("Nombre d'événements"),
        help_text=_("Nombre d'événements liés à cette formation")
    )
    
    dernier_commentaire = models.TextField(
        null=True, 
        blank=True, 
        verbose_name=_("Dernier commentaire"),
        help_text=_("Contenu du dernier commentaire ajouté")
    )

    partenaires = models.ManyToManyField(
        Partenaire, 
        related_name="formations", 
        verbose_name=_("Partenaires"), 
        blank=True,
        help_text=_("Partenaires associés à cette formation")
    )
    
    # Managers
    objects = FormationManager()

    def clean(self):
        """
        Validation des données avant sauvegarde.
        
        Raises:
            ValidationError: Si les données ne sont pas valides
        """
        super().clean()
        
        # Validation des dates
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError({
                'start_date': _("La date de début doit être antérieure à la date de fin."),
                'end_date': _("La date de fin doit être postérieure à la date de début."),
            })
            
        # Validation des places
        if self.inscrits_crif > self.prevus_crif and self.prevus_crif > 0:
            logger.warning(f"Inscrits CRIF ({self.inscrits_crif}) supérieurs aux prévus ({self.prevus_crif}) pour {self.nom}")
            
        if self.inscrits_mp > self.prevus_mp and self.prevus_mp > 0:
            logger.warning(f"Inscrits MP ({self.inscrits_mp}) supérieurs aux prévus ({self.prevus_mp}) pour {self.nom}")
            
        # Validation du nom
        if not self.nom.strip():
            raise ValidationError({'nom': _("Le nom de la formation ne peut pas être vide.")})

    def save(self, *args, **kwargs):
        """
        💾 Sauvegarde la formation avec journalisation des modifications.
        
        - Valide les données avec `full_clean()`
        - Utilise `transaction.atomic` pour la cohérence
        - Crée des entrées dans l'historique pour chaque champ modifié
        - Permet le suivi utilisateur via `user=...` dans `kwargs`
        
        Args:
            *args: Arguments positionnels pour super().save()
            **kwargs: Arguments nommés, notamment user
        """
        user = kwargs.pop("user", None)
        skip_history = kwargs.pop("skip_history", False)  # Option pour désactiver l'historique
        update_fields = kwargs.get("update_fields", None)  # Champs à mettre à jour
        
        is_new = self.pk is None
        original = None if is_new else self.__class__.objects.filter(pk=self.pk).first()
        
        # Validation des données
        self.full_clean()

        with transaction.atomic():
            # Transmission de l'utilisateur au BaseModel si fourni
            if user:
                self._user = user
                
            # Journalisation de l'action
            if is_new:
                logger.info(f"[Formation] Créée : {self.nom}")
            else:
                logger.info(f"[Formation] Modifiée : {self.nom} (#{self.pk})")
            
            # Sauvegarde
            super().save(*args, **kwargs)
            
            # Création de l'historique pour chaque champ modifié
            if not skip_history and original:
                self._create_history_entries(original, user, update_fields)

    def _create_history_entries(self, original, user, update_fields=None):
        """
        Crée des entrées d'historique pour les champs modifiés.
        
        Args:
            original (Formation): Instance originale avant modifications
            user (User): Utilisateur ayant effectué les modifications
            update_fields (list, optional): Liste des champs mis à jour
        """
        fields_to_check = update_fields or self.FIELDS_TO_TRACK
        
        for field in fields_to_check:
            if field not in self.FIELDS_TO_TRACK:
                continue
                
            old_val = getattr(original, field)
            new_val = getattr(self, field)
            
            if old_val != new_val:
                # Formatage des valeurs pour les champs spéciaux
                old_val_str = self._format_field_for_history(field, old_val)
                new_val_str = self._format_field_for_history(field, new_val)
                
                # Création de l'entrée d'historique
                HistoriqueFormation.objects.create(
                    formation=self,
                    champ_modifie=field,
                    ancienne_valeur=old_val_str,
                    nouvelle_valeur=new_val_str,
                    commentaire=f"Changement dans le champ {field}",
                    created_by=user,
                    details={"user": user.pk if user else None}
                )
                
                logger.debug(f"[Formation] Historique créé pour {field}: {old_val_str} → {new_val_str}")
    
    def _format_field_for_history(self, field_name, value):
        """
        Formate une valeur de champ pour l'historique.
        
        Args:
            field_name (str): Nom du champ
            value: Valeur à formater
            
        Returns:
            str: Valeur formatée pour l'historique
        """
        if value is None:
            return ""
            
        if isinstance(value, models.Model):
            return str(value.pk)
            
        if isinstance(value, (datetime.date, datetime.datetime)):
            return value.isoformat()
            
        return str(value)

    def to_serializable_dict(self):
        """
        📦 Retourne une représentation sérialisable pour API.
        
        Returns:
            dict: Données sérialisables de la formation
        """
        def convert_value(value):
            if isinstance(value, datetime.datetime):
                return value.strftime('%Y-%m-%d %H:%M')
            elif isinstance(value, datetime.date):
                return value.strftime('%Y-%m-%d')
            elif isinstance(value, models.Model):
                return {"id": value.pk, "nom": str(value)}
            return value

        # Données de base
        base_data = {key: convert_value(getattr(self, key)) for key in [
            "nom", "start_date", "end_date", "num_kairos", "num_offre", "num_produit",
            "prevus_crif", "prevus_mp", "inscrits_crif", "inscrits_mp", "assistante", "cap",
            "convocation_envoie", "entree_formation", "nombre_candidats",
            "nombre_entretiens", "nombre_evenements", "dernier_commentaire"
        ]}

        # Relations
        base_data.update({
            "id": self.pk,
            "centre": convert_value(self.centre),
            "type_offre": convert_value(self.type_offre),
            "statut": convert_value(self.statut),
            "statut_color": self.get_status_color(),
            "created_at": convert_value(self.created_at),
            "updated_at": convert_value(self.updated_at),
            "status_temporel": self.status_temporel,  # Ajout du statut temporel
        })

        # Propriétés calculées
        for prop in ["total_places", "total_inscrits", "taux_transformation", 
                    "taux_saturation", "places_disponibles", "is_a_recruter"]:
            base_data[prop] = getattr(self, prop)

        return base_data

    def __str__(self):
        """Représentation textuelle de la formation."""
        return f"{self.nom} ({self.centre.nom if self.centre else 'Centre inconnu'})"
        
    def __repr__(self):
        """Représentation technique pour le débogage."""
        return f"<Formation(id={self.pk}, nom='{self.nom}', statut='{self.statut}' if self.statut else 'None')>"

        
    def get_edit_url(self):
        """
        🔗 URL vers la page d'édition de la formation.
        
        Returns:
            str: URL de la page d'édition
        """
        return reverse('formation-edit', kwargs={'pk': self.pk})
        
    def get_delete_url(self):
        """
        🔗 URL vers la page de suppression de la formation.
        
        Returns:
            str: URL de la page de suppression
        """
        return reverse('formation-delete', kwargs={'pk': self.pk})

    # ===== Propriétés calculées =====
    
    @property
    def total_places(self): 
        """Nombre total de places disponibles (CRIF + MP)."""
        return self.prevus_crif + self.prevus_mp
        
    @property
    def total_inscrits(self): 
        """Nombre total d'inscrits (CRIF + MP)."""
        return self.inscrits_crif + self.inscrits_mp
        
    @property
    def places_restantes_crif(self): 
        """Places restantes pour CRIF."""
        return max(self.prevus_crif - self.inscrits_crif, 0)
        
    @property
    def places_restantes_mp(self): 
        """Places restantes pour MP."""
        return max(self.prevus_mp - self.inscrits_mp, 0)
        
    @property
    def places_disponibles(self): 
        """Nombre total de places encore disponibles."""
        return max(0, self.total_places - self.total_inscrits)
        
    @property
    def taux_saturation(self): 
        """Taux d'occupation des places en pourcentage."""
        return round(100.0 * self.total_inscrits / self.total_places, 2) if self.total_places else 0.0
        
    @property
    def taux_transformation(self): 
        """Taux de transformation candidats → inscrits."""
        return round(100.0 * self.total_inscrits / (self.nombre_candidats or 1), 2)
        
    @property
    def a_recruter(self): 
        """Nombre de places à pourvoir (legacy)."""
        return self.places_disponibles
        
    @property
    def is_a_recruter(self): 
        """Indique s'il reste des places disponibles."""
        return self.places_disponibles > 0
        
    @property
    def is_active(self):
        """
        Détermine si la formation est actuellement active.
        
        Returns:
            bool: True si la formation est en cours
        """
        today = timezone.now().date()
        return (self.start_date <= today <= self.end_date) if (self.start_date and self.end_date) else False
        
    @property
    def is_future(self):
        """
        Détermine si la formation n'a pas encore commencé.
        
        Returns:
            bool: True si la formation est à venir
        """
        today = timezone.now().date()
        return (self.start_date > today) if self.start_date else False
        
    @property
    def is_past(self):
        """
        Détermine si la formation est terminée.
        
        Returns:
            bool: True si la formation est terminée
        """
        today = timezone.now().date()
        return (self.end_date < today) if self.end_date else False
        
    @cached_property
    def status_temporel(self):
        """
        Statut temporel de la formation (actif, passé, futur).
        
        Returns:
            str: 'active', 'past', 'future' ou 'unknown'
        """
        if self.is_active:
            return 'active'
        elif self.is_future:
            return 'future'
        elif self.is_past:
            return 'past'
        return 'unknown'

    # ===== Méthodes d'ajout de contenu =====

    def add_commentaire(self, user, contenu: str, saturation=None):
            """
            Ajoute un commentaire à la formation.
            
            Args:
                user (User): Utilisateur créant le commentaire
                contenu (str): Texte du commentaire
                saturation (int, optional): Niveau de saturation (0-100)
                
            Returns:
                Commentaire: Instance du commentaire créé
            """
            from .commentaires import Commentaire
            
            # Validation de base
            if not contenu.strip():
                raise ValidationError("Le commentaire ne peut pas être vide.")
                
            # Création du commentaire
            commentaire = Commentaire.objects.create(
                formation=self,
                contenu=contenu,
                saturation=saturation,
                created_by=user
            )
            
            # Mise à jour du dernier commentaire
            ancien_commentaire = self.dernier_commentaire
            self.dernier_commentaire = contenu
            self.save(
                update_fields=['dernier_commentaire'], 
                skip_history=True
            )

            # Création de l'historique
            HistoriqueFormation.objects.create(
                formation=self,
                champ_modifie="dernier_commentaire",
                ancienne_valeur=ancien_commentaire or "",
                nouvelle_valeur=contenu,
                commentaire=f"Commentaire ajouté par {user.get_full_name() or user.username}",
                created_by=user
            )
            
            # Mise à jour de la saturation si fournie
            if saturation is not None:
                self.update_saturation_from_commentaires()
                
            return commentaire

    def add_document(self, user, fichier, titre: str, type_document=None):
        """
        Ajoute un document à la formation.

        Args:
            user (User): Utilisateur ajoutant le document.
            fichier (File): Fichier à téléverser.
            titre (str): Titre du document (nom lisible).
            type_document (str): Type du document (pdf, image, contrat, autre...).

        Returns:
            Document: Instance du document créé.
        """
        from .documents import Document
        from .formations import HistoriqueFormation

        # Validations
        if not titre or not titre.strip():
            raise ValidationError("Le titre du document ne peut pas être vide.")
        if not fichier:
            raise ValidationError("Aucun fichier fourni.")

        titre = titre.strip()

        # Création du document
        document = Document.objects.create(
            formation=self,
            fichier=fichier,
            nom_fichier=titre,
            type_document=type_document or Document.AUTRE,
            created_by=user
        )

        # Ajout dans l'historique
        HistoriqueFormation.objects.create(
            formation=self,
            champ_modifie="document",
            ancienne_valeur="—",
            nouvelle_valeur=titre,
            commentaire=f"Ajout du document « {titre} »",
            created_by=user
        )

        return document


    def add_evenement(self, type_evenement, event_date, details=None, description_autre=None, user=None):
        """
        Ajoute un événement à la formation.

        Args:
            type_evenement (str): Type d'événement (utiliser Evenement.TypeEvenement.*)
            event_date (date): Date de l'événement
            details (str, optional): Détails supplémentaires
            description_autre (str, optional): Description si type = 'autre'
            user (User, optional): Utilisateur créant l'événement

        Returns:
            Evenement: Instance de l'événement créé

        Raises:
            ValidationError: Si description manquante pour un événement de type 'Autre'
        """
        from .evenements import Evenement

        # Validation pour type 'autre'
        if type_evenement == Evenement.TypeEvenement.AUTRE and not description_autre:
            raise ValidationError("Veuillez fournir une description pour un événement de type 'Autre'.")

        # Création de l'événement
        evenement = Evenement.objects.create(
            formation=self,
            type_evenement=type_evenement,
            event_date=event_date,
            details=details,
            description_autre=description_autre if type_evenement == Evenement.TypeEvenement.AUTRE else None,
            created_by=user
        )

        # Mise à jour du compteur d'événements
        Formation.objects.filter(pk=self.pk).update(nombre_evenements=F('nombre_evenements') + 1)
        self.refresh_from_db(fields=['nombre_evenements'])


        # Création de l'historique
        event_date_str = event_date.strftime('%Y-%m-%d') if event_date else "Date non définie"
        type_display = (
            description_autre if type_evenement == Evenement.TypeEvenement.AUTRE
            else dict(Evenement.TypeEvenement.choices).get(type_evenement, type_evenement)
        )

        from .formations import HistoriqueFormation
        HistoriqueFormation.objects.create(
            formation=self,
            champ_modifie="evenement",
            nouvelle_valeur=f"{type_display} le {event_date_str}",
            commentaire="Ajout d'un événement",
            created_by=user
        )

        return evenement

    def add_partenaire(self, partenaire: Partenaire, user=None) -> None:
        """
        Ajoute un partenaire à la formation avec journalisation.
        
        Args:
            partenaire (Partenaire): Instance du partenaire à ajouter
            user (User, optional): Utilisateur effectuant l'ajout
        """
        if partenaire in self.partenaires.all():
            raise ValidationError(f"Le partenaire « {partenaire.nom} » est déjà lié à cette formation.")

        self.partenaires.add(partenaire)
        self.save(update_fields=[], skip_history=True)

        HistoriqueFormation.objects.create(
            formation=self,
            champ_modifie="partenaire",
            ancienne_valeur="—",
            nouvelle_valeur=partenaire.nom,
            commentaire=f"Ajout du partenaire « {partenaire.nom} »",
            created_by=user,
            action=HistoriqueFormation.ActionType.AJOUT
        )


    # ===== Méthodes de récupération de données liées =====
    
    def get_partenaires(self):
        """
        Récupère tous les partenaires liés à cette formation.
        
        Returns:
            QuerySet: Partenaires associés
        """
        return self.partenaires.all().prefetch_related()

    def get_commentaires(self, include_saturation=False, limit=None):
        """
        Récupère tous les commentaires liés à cette formation.
        Optimisé avec annotation optionnelle du niveau de saturation.
        
        Args:
            include_saturation (bool): Si True, inclut les commentaires avec saturation non nulle
            limit (int, optional): Limite le nombre de commentaires retournés
            
        Returns:
            QuerySet: Commentaires triés par date (plus récents en premier)
        """
        queryset = self.commentaires.select_related("created_by")
        
        # Filtrer les commentaires avec saturation si demandé
        if include_saturation:
            queryset = queryset.filter(saturation__isnull=False)
            
        # Appliquer le tri standard
        queryset = queryset.order_by('-created_at')
        
        # Limiter le nombre de résultats si nécessaire
        if limit is not None:
            queryset = queryset[:limit]
            
        return queryset

    def get_evenements(self):
        """
        Récupère tous les événements liés à cette formation.
        
        Returns:
            QuerySet: Événements triés par date (plus récents en premier)
        """
        return self.evenements.select_related("created_by").order_by('-event_date')

    def get_documents(self, est_public=None):
        """
        Récupère tous les documents liés à cette formation.
        
        Args:
            est_public (bool, optional): Si spécifié, filtre les documents publics/privés
            
        Returns:
            QuerySet: Documents associés
        """
        queryset = self.documents.select_related("uploaded_by")
        
        # Filtrer par visibilité si spécifié
        if est_public is not None:
            queryset = queryset.filter(est_public=est_public)
            
        return queryset

    def get_prospections(self):
        """
        Retourne toutes les prospections liées à cette formation.

        Returns:
            QuerySet[Prospection]: Liste des prospections liées.
        """
        return self.prospection_set.all()

    def get_historique(self, limit=None):
        """
        Récupère l'historique des modifications de cette formation.
        
        Args:
            limit (int, optional): Nombre maximum d'entrées à retourner
            
        Returns:
            QuerySet: Entrées d'historique triées par date (plus récentes en premier)
        """
        queryset = self.historiques.select_related("created_by").order_by('-created_at')
        return queryset[:limit] if limit else queryset

    # ===== Méthodes de calcul et mise à jour =====

    def update_saturation_from_commentaires(self):
        """
        Met à jour le niveau de saturation moyen basé sur les commentaires.
        
        Returns:
            bool: True si la mise à jour a été effectuée
        """
        from .commentaires import Commentaire
        
        # Récupération des valeurs de saturation
        saturations = Commentaire.objects.filter(
            formation=self,
            saturation__isnull=False
        ).values_list('saturation', flat=True)
        
        # Calcul de la moyenne si des données existent
        if saturations:
            self.saturation = round(sum(saturations) / len(saturations), 2)
            self.save(update_fields=['saturation'])
            logger.info(f"[Formation] Saturation mise à jour pour {self.nom}: {self.saturation}%")
            return True
            
        return False

    def get_saturation_moyenne_commentaires(self):
        """
        Calcule la saturation moyenne basée sur les commentaires.
        
        Returns:
            float: Saturation moyenne ou None
        """
        from .commentaires import Commentaire
        
        saturations = Commentaire.objects.filter(
            formation=self,
            saturation__isnull=False
        ).values_list('saturation', flat=True)
        
        return round(sum(saturations) / len(saturations), 2) if saturations else None

    def get_status_color(self):
        """
        Retourne la couleur associée au statut de la formation.
        
        Returns:
            str: Code couleur CSS
        """
        return self.statut.couleur if self.statut and self.statut.couleur else get_default_color(self.statut.nom if self.statut else "")
    
    def duplicate(self, user=None, **kwargs):
        """
        Crée une copie de cette formation avec possibilité de modifier certains champs.
        
        Args:
            user (User, optional): Utilisateur effectuant la duplication
            **kwargs: Champs à modifier dans la copie
            
        Returns:
            Formation: Nouvelle instance de formation
        """
        # Exclure les champs qui ne doivent pas être copiés
        exclude_fields = ['id', 'pk', 'created_at', 'updated_at', 'created_by', 
                          'updated_by', 'dernier_commentaire', 'nombre_candidats',
                          'nombre_entretiens', 'nombre_evenements']
        
        # Créer un dictionnaire avec les valeurs des champs à copier
        field_dict = {f.name: getattr(self, f.name) 
                     for f in self._meta.fields 
                     if f.name not in exclude_fields}
        
        # Appliquer les modifications spécifiées
        field_dict.update(kwargs)
        
        # Par défaut, ajouter "(Copie)" au nom si non spécifié
        if 'nom' not in kwargs:
            field_dict['nom'] = f"{self.nom} (Copie)"
        
        # Créer la nouvelle instance
        new_formation = Formation.objects.create(**field_dict)
        
        # Copier les relations many-to-many si nécessaire
        new_formation.partenaires.set(self.partenaires.all())
        
        # Journaliser la duplication
        HistoriqueFormation.objects.create(
            formation=new_formation,
            champ_modifie="creation",
            nouvelle_valeur="Duplication",
            commentaire=f"Dupliqué depuis la formation #{self.pk}: {self.nom}",
            created_by=user,
            action=HistoriqueFormation.ActionType.AJOUT
        )
        
        return new_formation
    
    @classmethod
    def get_csv_fields(cls):
        """
        Liste des champs à inclure dans un export CSV/Excel.
        
        Returns:
            list: Noms des champs
        """
        return [
            'id', 'nom', 'centre', 'type_offre', 'statut', 'start_date', 'end_date',
        'num_kairos', 'num_offre', 'num_produit', 'prevus_crif', 'prevus_mp',
        'inscrits_crif', 'inscrits_mp', 'assistante', 'cap', 'convocation_envoie',
        'entree_formation',
        ]

    @classmethod
    def get_csv_headers(cls):
        return [
            'ID', 'Nom', 'Centre', 'Type d\'offre', 'Statut',
            'Date de début', 'Date de fin', 'Num Kairos', 'Num Offre', 'Num Produit',
            'Places CRIF', 'Places MP', 'Inscrits CRIF', 'Inscrits MP',
            'Assistante', 'CAP', 'Convocation envoyée', 'Entrée en formation'
        ]

    def to_csv_row(self):
        return [
            self.pk,
            self.nom,
            self.centre.nom if self.centre else '',
            self.type_offre.nom if self.type_offre else '',
            self.statut.nom if self.statut else '',
            self.start_date.strftime('%d/%m/%Y') if self.start_date else '',
            self.end_date.strftime('%d/%m/%Y') if self.end_date else '',
            self.num_kairos or '',
            self.num_offre or '',
            self.num_produit or '',
            self.prevus_crif,
            self.prevus_mp,
            self.inscrits_crif,
            self.inscrits_mp,
            self.assistante or '',
            self.cap or '',
            self.convocation_envoie,
            self.entree_formation,         ]
        
    @classmethod
    def get_stats_par_mois(cls, annee=None):
        """
        Calcule des statistiques mensuelles sur les formations.
        
        Args:
            annee (int, optional): Année pour les statistiques, par défaut l'année en cours
            
        Returns:
            dict: Statistiques par mois
        """
        annee = annee or timezone.now().year
        
        # Préparation du dictionnaire de résultat
        mois_labels = [
            "Janvier", "Février", "Mars", "Avril", "Mai", "Juin", 
            "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
        ]
        result = {i+1: {"label": mois_labels[i], "count": 0, "inscrits": 0} for i in range(12)}
        
        # Requête pour compter les formations par mois
        formations_par_mois = cls.objects.filter(
            start_date__year=annee
        ).values(
            'start_date__month'
        ).annotate(
            count=Count('id'),
            inscrits=Sum(F('inscrits_crif') + F('inscrits_mp'))
        )
        
        # Remplissage des résultats
        for item in formations_par_mois:
            mois = item['start_date__month']
            if mois in result:
                result[mois]["count"] = item['count']
                result[mois]["inscrits"] = item['inscrits'] or 0
                
        return result

    class Meta:
        verbose_name = _("Formation")
        verbose_name_plural = _("Formations")
        ordering = ['-start_date', 'nom']
        indexes = [
            models.Index(fields=['start_date'], name='form_start_date_idx'),
            models.Index(fields=['end_date'], name='form_end_date_idx'),
            models.Index(fields=['nom'], name='form_nom_idx'),
            models.Index(fields=['statut'], name='form_statut_idx'),
            models.Index(fields=['type_offre'], name='form_type_offre_idx'),
            models.Index(fields=['convocation_envoie'], name='form_convoc_idx'),
            models.Index(fields=['centre'], name='form_centre_idx'),
            models.Index(fields=['start_date', 'end_date'], name='form_dates_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(
                    Q(start_date__isnull=True) | 
                    Q(end_date__isnull=True) | 
                    Q(start_date__lte=F('end_date'))
                ),
                name="formation_dates_coherentes"
            )
        ]


class HistoriqueFormation(BaseModel):
    """
    🕓 Historique de modification d'une formation.

    Ce modèle trace tous les changements appliqués à une formation, champ par champ,
    avec la date, l'utilisateur et un commentaire facultatif.
    
    Attributs:
        formation (Formation): Formation concernée par la modification
        action (str): Type d'action (modification, ajout, suppression)
        champ_modifie (str): Nom du champ modifié
        ancienne_valeur (str): Valeur avant modification
        nouvelle_valeur (str): Valeur après modification
        commentaire (str): Commentaire explicatif
        details (dict): Données contextuelles supplémentaires
        
    Propriétés:
        utilisateur_nom (str): Nom de l'utilisateur ayant fait la modification
    """
    
    # Constantes pour les limites de champs
    ACTION_MAX_LENGTH = 100
    CHAMP_MAX_LENGTH = 100
    
    # Choix pour le type d'action
    class ActionType(models.TextChoices):
        MODIFICATION = 'modification', _('Modification')
        AJOUT = 'ajout', _('Ajout')
        SUPPRESSION = 'suppression', _('Suppression')
        COMMENTAIRE = 'commentaire', _('Commentaire')
        DOCUMENT = 'document', _('Document')
        EVENEMENT = 'evenement', _('Événement')

    formation = models.ForeignKey(
        'Formation',
        on_delete=models.CASCADE,
        related_name="historiques",
        verbose_name=_("Formation concernée"),
        help_text=_("Formation à laquelle ce changement est associé")
    )

    action = models.CharField(
        max_length=ACTION_MAX_LENGTH,
        choices=ActionType.choices,
        default=ActionType.MODIFICATION,
        verbose_name=_("Type d'action"),
        help_text=_("Nature de l'action réalisée (ex : modification, ajout)")
    )

    champ_modifie = models.CharField(
        max_length=CHAMP_MAX_LENGTH,
        verbose_name=_("Champ modifié"),
        help_text=_("Nom du champ ayant été modifié")
    )

    ancienne_valeur = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Ancienne valeur"),
        help_text=_("Valeur avant la modification")
    )

    nouvelle_valeur = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Nouvelle valeur"),
        help_text=_("Valeur après la modification")
    )

    commentaire = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Commentaire de modification"),
        help_text=_("Commentaire explicatif (facultatif)")
    )

    details = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Détails supplémentaires"),
        help_text=_("Données contextuelles (ex : ID utilisateur, origine, etc.)")
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Historique de modification de formation")
        verbose_name_plural = _("Historiques de modifications de formations")
        indexes = [
            models.Index(fields=['-created_at'], name='hist_form_date_idx'),
            models.Index(fields=['formation'], name='hist_form_formation_idx'),
            models.Index(fields=['action'], name='hist_form_action_idx'),
            models.Index(fields=['champ_modifie'], name='hist_form_champ_idx'),
        ]

    def __str__(self):
        """Représentation textuelle de l'entrée d'historique."""
        return f"Modification de {self.champ_modifie} le {self.created_at.strftime('%d/%m/%Y à %H:%M')}"

    def save(self, *args, **kwargs):
        """
        Sauvegarde l'entrée d'historique de formation dans une transaction atomique.

        Cette méthode surcharge `save()` pour garantir que chaque création ou mise à jour
        d'une instance de `HistoriqueFormation` est encapsulée dans une transaction.
        Elle vérifie également les doublons potentiels (même champ modifié, même utilisateur,
        même valeur dans un intervalle court) pour éviter la duplication d'entrées.

        Args:
            *args: Arguments positionnels transmis à `super().save()`.
            **kwargs: Arguments nommés transmis à `super().save()`, notamment:
                skip_duplicate_check (bool): Si True, désactive la vérification des doublons

        Returns:
            bool: True si sauvegardé, False si doublon détecté et ignoré
        """
        skip_duplicate_check = kwargs.pop("skip_duplicate_check", False)
        
        # Vérification des doublons seulement pour les nouvelles entrées
        if not skip_duplicate_check and not self.pk:
            # Intervalle de temps pour considérer les mises à jour comme doublons (5 minutes par défaut)
            time_threshold = kwargs.pop("time_threshold", timezone.timedelta(minutes=5))
            cutoff_time = timezone.now() - time_threshold
            
            # Recherche des entrées similaires récentes
            recent_similar = HistoriqueFormation.objects.filter(
                formation=self.formation,
                champ_modifie=self.champ_modifie,
                created_by=self.created_by,
                nouvelle_valeur=self.nouvelle_valeur,
                created_at__gte=cutoff_time
            ).exists()
            
            if recent_similar:
                logger.info(f"[Historique] Doublon ignoré: {self.champ_modifie} pour {self.formation}")
                return False

        with transaction.atomic():
            super().save(*args, **kwargs)
        
        logger.info(f"[Historique] {self}")
        return True


    def to_serializable_dict(self):
        """
        📦 Représentation JSON de l'entrée d'historique.

        Returns:
            dict: Contenu API-friendly.
        """
        return {
            "id": self.pk,
            "formation_id": self.formation_id,
            "formation_nom": str(self.formation),
            "champ": self.champ_modifie,
            "ancienne_valeur": self.ancienne_valeur,
            "nouvelle_valeur": self.nouvelle_valeur,
            "commentaire": self.commentaire,
            "action": self.action,
            "action_display": self.get_action_display(),
            "created_at": self.created_at.strftime('%Y-%m-%d %H:%M'),
            "utilisateur": self.utilisateur_nom,
            "details": self.details,
        }

    @property
    def utilisateur_nom(self):
        """
        👤 Nom de l'utilisateur ayant réalisé la modification.
        
        Returns:
            str: Nom complet de l'utilisateur ou "Inconnu"
        """
        if self.created_by:
            return f"{self.created_by.first_name} {self.created_by.last_name}".strip() or self.created_by.username
        return "Inconnu"
        
    @property
    def valeur_changement(self):
        """
        💫 Récupère une représentation du changement effectué.
        
        Returns:
            str: Représentation du changement
        """
        if self.ancienne_valeur and self.nouvelle_valeur:
            return f"{self.ancienne_valeur} → {self.nouvelle_valeur}"
        elif self.nouvelle_valeur:
            return f"Ajout: {self.nouvelle_valeur}"
        elif self.ancienne_valeur:
            return f"Suppression: {self.ancienne_valeur}"
        return "Aucun changement spécifié"
        
    @classmethod
    def get_latest_changes(cls, limit=10):
        """
        Récupère les derniers changements, toutes formations confondues.
        
        Args:
            limit (int): Nombre maximum de changements à retourner
            
        Returns:
            QuerySet: Derniers changements
        """
        return cls.objects.select_related('formation', 'created_by').order_by('-created_at')[:limit]