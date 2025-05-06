import datetime
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import F
from .base import BaseModel  # ajuste le chemin selon ton projet

from .partenaires import Partenaire
from .centres import Centre
from .types_offre import TypeOffre
from .base import BaseModel
from .statut import Statut, get_default_color


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
            "end_date", "-end_date"
        ]
        return self.get_queryset().order_by(champ_tri) if champ_tri in champs_autorises else self.get_queryset()


class Formation(BaseModel):
    """
    Représente une formation avec toutes ses caractéristiques.
    
    Ce modèle est au cœur du système et contient toutes les informations nécessaires
    pour gérer les formations, leur recrutement, et leur suivi.
    
    Pour la sérialisation, les champs suivants sont importants:
    - Tous les champs de données principales (nom, centre, dates, etc.)
    - Les propriétés calculées (total_places, taux_saturation, etc.)
    - Les relations avec d'autres modèles (partenaires, commentaires, événements)
    """

    # Informations générales
    nom = models.CharField(max_length=255, verbose_name="Nom de la formation")
    centre = models.ForeignKey(
        Centre, 
        on_delete=models.CASCADE, 
        related_name='formations', 
        verbose_name="Centre de formation"
    )
    type_offre = models.ForeignKey(
        TypeOffre, 
        on_delete=models.CASCADE, 
        related_name="formations", 
        verbose_name="Type d'offre"
    )
    statut = models.ForeignKey(
        Statut, 
        on_delete=models.CASCADE, 
        related_name="formations", 
        verbose_name="Statut de la formation"
    )

    # Dates et identifiants
    start_date = models.DateField(null=True, blank=True, verbose_name="Date de début")
    end_date = models.DateField(null=True, blank=True, verbose_name="Date de fin")
    num_kairos = models.CharField(max_length=50, null=True, blank=True, verbose_name="Numéro Kairos")
    num_offre = models.CharField(max_length=50, null=True, blank=True, verbose_name="Numéro de l'offre")
    num_produit = models.CharField(max_length=50, null=True, blank=True, verbose_name="Numéro du produit")

    # Gestion des places et inscriptions
    prevus_crif = models.PositiveIntegerField(default=0, verbose_name="Places prévues CRIF")
    prevus_mp = models.PositiveIntegerField(default=0, verbose_name="Places prévues MP")
    inscrits_crif = models.PositiveIntegerField(default=0, verbose_name="Inscrits CRIF")
    inscrits_mp = models.PositiveIntegerField(default=0, verbose_name="Inscrits MP")

    saturation = models.FloatField(
        null=True, 
        blank=True, 
        verbose_name="Niveau de saturation moyen",
        help_text="Pourcentage moyen de saturation basé sur les commentaires"
    )
    
    # Informations supplémentaires
    assistante = models.CharField(max_length=255, null=True, blank=True, verbose_name="Assistante")
    cap = models.PositiveIntegerField(null=True, blank=True, verbose_name="Capacité maximale")
    convocation_envoie = models.BooleanField(default=False, verbose_name="Convocation envoyée")
    entresformation = models.PositiveIntegerField(default=0, verbose_name="Entrées en formation")

    # Statistiques de recrutement
    nombre_candidats = models.PositiveIntegerField(default=0, verbose_name="Nombre de candidats")
    nombre_entretiens = models.PositiveIntegerField(default=0, verbose_name="Nombre d'entretiens")
    nombre_evenements = models.PositiveIntegerField(default=0, verbose_name="Nombre d'événements")
    dernier_commentaire = models.TextField(null=True, blank=True, verbose_name="Dernier commentaire")

    # Relations
    partenaires = models.ManyToManyField(
        Partenaire, 
        related_name="formations", 
        verbose_name="Partenaires", 
        blank=True
    )


    # Manager personnalisé
    objects = FormationManager()

    def clean(self):
        """
        Vérifie la cohérence des données avant la sauvegarde.
        Déclenche une ValidationError si les données sont incorrectes.
        """
        super().clean()
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError("La date de début doit être antérieure à la date de fin.")

    def save(self, *args, **kwargs):
        """
        Sauvegarde la formation et crée des entrées d'historique pour les champs modifiés.
        Utilise une transaction pour garantir l'intégrité des données.
        """
        with transaction.atomic():
            is_new = self.pk is None
            
            # Récupération de l'ancienne instance avec préchargement des relations
            old_instance = None
            if not is_new:
                old_instance = Formation.objects.select_related(
                    'centre', 'type_offre', 'statut'
                ).filter(pk=self.pk).first()
            
            # Sauvegarde principale
            super().save(*args, **kwargs)

            # Création des entrées d'historique pour les champs modifiés
            if old_instance:
                fields_to_track = [
                    'nom', 'centre', 'type_offre', 'statut', 'start_date', 'end_date',
                    'num_kairos', 'num_offre', 'num_produit', 'prevus_crif', 'prevus_mp',
                    'inscrits_crif', 'inscrits_mp', 'assistante', 'cap', 'convocation_envoie',
                    'entresformation', 'nombre_candidats', 'nombre_entretiens', 'dernier_commentaire'
                ]
                for field in fields_to_track:
                    old_val = getattr(old_instance, field)
                    new_val = getattr(self, field)
                    if old_val != new_val:
                        HistoriqueFormation.objects.create(
                            formation=self,
                            champ_modifie=field,
                            ancienne_valeur=str(old_val.pk if isinstance(old_val, models.Model) else old_val),
                            nouvelle_valeur=str(new_val.pk if isinstance(new_val, models.Model) else new_val),
                            modifie_par=self.utilisateur
                        )

    def to_serializable_dict(self):
        """
        Retourne un dictionnaire JSON-sérialisable des valeurs de la formation.
        Utile pour les API REST et la sérialisation.
        
        Returns:
            dict: Dictionnaire des valeurs de la formation, avec les dates et objets
                 convertis en format sérialisable
        """
        def convert_value(value):
            if isinstance(value, (datetime.date, datetime.datetime)):
                return value.strftime('%Y-%m-%d')
            elif isinstance(value, models.Model):
                return {
                    'id': value.pk,
                    'name': str(value)
                }
            return value

        base_data = {key: convert_value(getattr(self, key)) for key in [
            "nom", "centre", "type_offre", "statut", "start_date", "end_date", 
            "num_kairos", "num_offre", "num_produit", "prevus_crif", "prevus_mp", 
            "inscrits_crif", "inscrits_mp", "assistante", "cap", "convocation_envoie",
            "entresformation", "nombre_candidats", "nombre_entretiens", 
            "nombre_evenements", "dernier_commentaire"
        ]}
        
        # Ajout des propriétés calculées
        computed_properties = [
            "total_places", "total_inscrits", "taux_transformation", 
            "taux_saturation", "places_disponibles", "is_a_recruter"
        ]
        for prop in computed_properties:
            base_data[prop] = getattr(self, prop)
            
        return base_data

    @property
    def total_places(self):
        """
        Retourne le nombre total de places prévues (CRIF + MP).
        
        Returns:
            int: Somme des places prévues
        """
        return self.prevus_crif + self.prevus_mp

    @property
    def total_inscrits(self):
        """
        Retourne le nombre total d'inscrits (CRIF + MP).
        
        Returns:
            int: Somme des inscrits
        """
        return self.inscrits_crif + self.inscrits_mp

    @property
    def taux_transformation(self):
        """
        Calcule le taux de transformation (inscrits / candidats).
        
        Returns:
            float: Pourcentage des candidats devenus inscrits (0-100)
        """
        total_candidats = self.nombre_candidats or 0
        return round(100.0 * self.total_inscrits / total_candidats, 2) if total_candidats > 0 else 0.0

    @property
    def taux_saturation(self):
        """
        Calcule le taux de saturation (inscrits / places prévues).
        
        Returns:
            float: Pourcentage de remplissage (0-100)
        """
        return round(100.0 * self.total_inscrits / self.total_places, 2) if self.total_places > 0 else 0.0

    @property
    def places_restantes_crif(self):
        """
        Calcule le nombre de places restantes pour le CRIF.
        
        Returns:
            int: Nombre de places CRIF disponibles
        """
        return max(self.prevus_crif - self.inscrits_crif, 0)

    @property
    def places_restantes_mp(self):
        """
        Calcule le nombre de places restantes pour MP.
        
        Returns:
            int: Nombre de places MP disponibles
        """
        return max(self.prevus_mp - self.inscrits_mp, 0)

    @property
    def places_disponibles(self):
        """
        Retourne le nombre total de places encore disponibles.
        
        Returns:
            int: Total des places disponibles
        """
        return max(0, self.total_places - self.total_inscrits)

    @property
    def a_recruter(self):
        """
        Alias pour places_disponibles.
        
        Returns:
            int: Nombre de places à recruter
        """
        return self.places_disponibles

    @property
    def is_a_recruter(self):
        """
        Indique si la formation a encore des places disponibles.
        
        Returns:
            bool: True si des places sont disponibles, False sinon
        """
        return self.places_disponibles > 0

    def add_commentaire(self, utilisateur, contenu):
        """
        Ajoute un commentaire à la formation et met à jour le dernier commentaire.
        Crée également une entrée dans l'historique pour tracer cette action.
        
        Args:
            utilisateur (User): Utilisateur qui ajoute le commentaire
            contenu (str): Texte du commentaire
            
        Returns:
            Commentaire: L'instance du commentaire créé
        """
        commentaire = self.commentaires.create(
            utilisateur=utilisateur,
            contenu=contenu
        )
        
        # Mise à jour du dernier commentaire
        ancien_commentaire = self.dernier_commentaire
        self.dernier_commentaire = contenu
        self.save(update_fields=['dernier_commentaire'])
        
        # Ajout d'une entrée dans l'historique
        
        HistoriqueFormation.objects.create(
            formation=self,
            champ_modifie="commentaire",
            ancienne_valeur=ancien_commentaire or "",
            nouvelle_valeur=contenu,
            modifie_par=utilisateur,
            action="ajout_commentaire",
            commentaire=f"Commentaire ajouté par {utilisateur.username if utilisateur else 'Anonyme'}"
        )
        
        return commentaire

    def add_evenement(self, type_evenement, event_date, details=None, description_autre=None):
        """
        Ajoute un événement à la formation et incrémente le compteur d'événements.
        
        Args:
            type_evenement (str): Type d'événement (choix défini dans le modèle Evenement)
            event_date (date): Date de l'événement
            details (str, optional): Détails supplémentaires
            description_autre (str, optional): Description pour les événements de type 'Autre'
            
        Returns:
            Evenement: L'instance de l'événement créé
            
        Raises:
            ValidationError: Si un type 'Autre' est spécifié sans description
        """
        from .evenements import Evenement
        
        if type_evenement == Evenement.AUTRE and not description_autre:
            raise ValidationError("Veuillez fournir une description pour un événement de type 'Autre'.")
            
        evenement = Evenement.objects.create(
            formation=self,
            type_evenement=type_evenement,
            event_date=event_date,
            details=details,
            description_autre=description_autre if type_evenement == Evenement.AUTRE else None
        )
        
        # Utilisation de F() pour éviter les problèmes de concurrence
        self.nombre_evenements = F('nombre_evenements') + 1
        self.save(update_fields=['nombre_evenements'])
        
        # Rechargement de l'instance pour avoir le nombre correct
        self.refresh_from_db(fields=['nombre_evenements'])
        
        return evenement

    def get_saturation_moyenne_commentaires(self):
        """
        Calcule la moyenne des saturations mentionnées dans les commentaires.
        
        Returns:
            float or None: Moyenne des saturations ou None si aucune saturation n'est trouvée
        """
        saturations = self.commentaires.exclude(saturation__isnull=True).values_list('saturation', flat=True)
        if saturations:
            return round(sum(saturations) / len(saturations), 2)
        return None

    def get_status_color(self):
        """
        Retourne la couleur associée au statut de la formation.
        
        Returns:
            str: Code couleur (hex ou nom)
        """
        return self.statut.couleur if self.statut.couleur else get_default_color(self.statut.nom)

    def get_absolute_url(self):
        """
        Retourne l'URL de détail de la formation.
        
        Returns:
            str: URL vers la page de détail
        """
        return reverse('formation-detail', kwargs={'pk': self.pk})

    def get_commentaires(self):
        """
        Retourne tous les commentaires associés à cette formation, avec leurs auteurs.
        
        Returns:
            QuerySet: Commentaires triés par date de création décroissante
        """
        return self.commentaires.select_related("utilisateur").order_by('-created_at')

    def get_evenements(self):
        """
        Retourne tous les événements associés à cette formation.
        
        Returns:
            QuerySet: Événements associés
        """
        return self.evenements.all().order_by('-event_date')

    def get_documents(self):
        """
        Retourne tous les documents associés à cette formation.
        
        Returns:
            QuerySet: Documents associés
        """
        return self.documents.all()

    def get_partenaires(self):
        """
        Retourne les partenaires associés à cette formation.
        
        Returns:
            QuerySet: Partenaires associés
        """
        return self.partenaires.all().prefetch_related()

    def __str__(self):
        """
        Représentation textuelle de la formation.
        
        Returns:
            str: Nom de la formation et centre
        """
        return f"{self.nom} ({self.centre.nom if self.centre else 'Centre inconnu'})"

    class Meta:
        verbose_name = "Formation"
        verbose_name_plural = "Formations"
        ordering = ['-start_date', 'nom']
        indexes = [
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
            models.Index(fields=['nom']),
        ]


class HistoriqueFormation(BaseModel):
    """
    Historique de modification d'une formation.

    Ce modèle trace les changements champ par champ d'une formation,
    avec l'utilisateur ayant effectué la modification.
    Hérite de BaseModel pour le timestamping et le tracking générique.
    """

    formation = models.ForeignKey(
        'Formation',
        on_delete=models.CASCADE,
        related_name="historiques",
        verbose_name="Formation concernée"
    )

    action = models.CharField(
        max_length=100,
        default='modification',
        verbose_name="Type d'action"
    )

    champ_modifie = models.CharField(
        max_length=100,
        verbose_name="Champ modifié"
    )

    ancienne_valeur = models.TextField(
        null=True,
        blank=True,
        verbose_name="Ancienne valeur"
    )

    nouvelle_valeur = models.TextField(
        null=True,
        blank=True,
        verbose_name="Nouvelle valeur"
    )

    commentaire = models.TextField(
        null=True,
        blank=True,
        verbose_name="Commentaire de modification"
    )

    details = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Détails supplémentaires"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Historique de modification de formation"
        verbose_name_plural = "Historiques de modifications de formations"
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['formation']),
        ]

    def __str__(self):
        return f"Modification de {self.champ_modifie} le {self.created_at.strftime('%d/%m/%Y à %H:%M')}"

    @property
    def utilisateur_nom(self):
        if self.modifie_par:
            return f"{self.modifie_par.first_name} {self.modifie_par.last_name}".strip() or self.modifie_par.username
        return "Inconnu"
