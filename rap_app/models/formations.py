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
    # Informations générales
    nom = models.CharField(max_length=255, verbose_name="Nom de la formation")
    centre = models.ForeignKey(Centre, on_delete=models.CASCADE, related_name='formations', verbose_name="Centre de formation")
    type_offre = models.ForeignKey(TypeOffre, on_delete=models.CASCADE, related_name="formations", verbose_name="Type d'offre")
    statut = models.ForeignKey(Statut, on_delete=models.CASCADE, related_name="formations", verbose_name="Statut de la formation")

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
        null=True, blank=True, verbose_name="Niveau de saturation moyen",
        help_text="Pourcentage moyen de saturation basé sur les commentaires"
    )

    # Informations supplémentaires
    assistante = models.CharField(max_length=255, null=True, blank=True, verbose_name="Assistante")
    cap = models.PositiveIntegerField(null=True, blank=True, verbose_name="Capacité maximale")
    convocation_envoie = models.BooleanField(default=False, verbose_name="Convocation envoyée")
    entree_formation = models.PositiveIntegerField(default=0, verbose_name="Entrées en formation")

    # Statistiques de recrutement
    nombre_candidats = models.PositiveIntegerField(default=0, verbose_name="Nombre de candidats")
    nombre_entretiens = models.PositiveIntegerField(default=0, verbose_name="Nombre d'entretiens")
    nombre_evenements = models.PositiveIntegerField(default=0, verbose_name="Nombre d'événements")
    dernier_commentaire = models.TextField(null=True, blank=True, verbose_name="Dernier commentaire")

    partenaires = models.ManyToManyField(
        Partenaire, related_name="formations", verbose_name="Partenaires", blank=True
    )

    objects = FormationManager()

    def clean(self):
        super().clean()
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError({
                'start_date': "La date de début doit être antérieure à la date de fin.",
                'end_date': "La date de fin doit être postérieure à la date de début.",
            })

    def save(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        is_new = self.pk is None
        original = None if is_new else self.__class__.objects.filter(pk=self.pk).first()
        self.full_clean()

        import logging
        logger = logging.getLogger("application.formation")

        with transaction.atomic():
            if user:
                self._user = user
            if is_new:
                logger.info(f"[Formation] Créée : {self.nom}")
            else:
                logger.info(f"[Formation] Modifiée : {self.nom} ({self.pk})")
            super().save(user=user, *args, **kwargs)

            if original:
                fields_to_track = [
                    'nom', 'centre', 'type_offre', 'statut', 'start_date', 'end_date',
                    'num_kairos', 'num_offre', 'num_produit', 'prevus_crif', 'prevus_mp',
                    'inscrits_crif', 'inscrits_mp', 'assistante', 'cap', 'convocation_envoie',
                    'entree_formation', 'nombre_candidats', 'nombre_entretiens', 'dernier_commentaire'
                ]
                for field in fields_to_track:
                    old_val = getattr(original, field)
                    new_val = getattr(self, field)
                    if old_val != new_val:
                        HistoriqueFormation.objects.create(
                            formation=self,
                            champ_modifie=field,
                            ancienne_valeur=str(old_val.pk if isinstance(old_val, models.Model) else old_val),
                            nouvelle_valeur=str(new_val.pk if isinstance(new_val, models.Model) else new_val),
                            commentaire=f"Changement automatique dans le champ {field}",
                            created_by=user,
                            details={"user": user.pk if user else None}
                        )

    def to_serializable_dict(self):
        def convert_value(value):
            if isinstance(value, datetime.datetime):
                return value.strftime('%Y-%m-%d %H:%M')
            elif isinstance(value, datetime.date):
                return value.strftime('%Y-%m-%d')
            elif isinstance(value, models.Model):
                return {"id": value.pk, "nom": str(value)}
            return value

        base_data = {key: convert_value(getattr(self, key)) for key in [
            "nom", "start_date", "end_date", "num_kairos", "num_offre", "num_produit",
            "prevus_crif", "prevus_mp", "inscrits_crif", "inscrits_mp", "assistante", "cap",
            "convocation_envoie", "entree_formation", "nombre_candidats",
            "nombre_entretiens", "nombre_evenements", "dernier_commentaire"
        ]}

        base_data.update({
            "centre": convert_value(self.centre),
            "type_offre": convert_value(self.type_offre),
            "statut": convert_value(self.statut),
        })

        for prop in ["total_places", "total_inscrits", "taux_transformation", "taux_saturation", "places_disponibles", "is_a_recruter"]:
            base_data[prop] = getattr(self, prop)

        return base_data

    def __str__(self):
        return f"{self.nom} ({self.centre.nom if self.centre else 'Centre inconnu'})"

    def get_absolute_url(self):
        return reverse('formation-detail', kwargs={'pk': self.pk})

    @property
    def total_places(self): return self.prevus_crif + self.prevus_mp
    @property
    def total_inscrits(self): return self.inscrits_crif + self.inscrits_mp
    @property
    def places_restantes_crif(self): return max(self.prevus_crif - self.inscrits_crif, 0)
    @property
    def places_restantes_mp(self): return max(self.prevus_mp - self.inscrits_mp, 0)
    @property
    def places_disponibles(self): return max(0, self.total_places - self.total_inscrits)
    @property
    def taux_saturation(self): return round(100.0 * self.total_inscrits / self.total_places, 2) if self.total_places else 0.0
    @property
    def taux_transformation(self): return round(100.0 * self.total_inscrits / (self.nombre_candidats or 1), 2)
    @property
    def a_recruter(self): return self.places_disponibles
    @property
    def is_a_recruter(self): return self.places_disponibles > 0

    def add_commentaire(self, user, contenu: str):
        commentaire = self.commentaires.create(contenu=contenu, created_by=user)
        ancien_commentaire = self.dernier_commentaire
        self.dernier_commentaire = contenu
        self.save(update_fields=['dernier_commentaire'])

        HistoriqueFormation.objects.create(
            formation=self,
            champ_modifie="dernier_commentaire",
            ancienne_valeur=ancien_commentaire or "",
            nouvelle_valeur=contenu,
            commentaire=f"Commentaire ajouté par {user.get_full_name() or user.username}",
            created_by=user
        )
        return commentaire

    def add_document(self, user, fichier, titre: str, est_public: bool = False):
        from .documents import Document
        document = Document.objects.create(
            formation=self,
            fichier=fichier,
            titre=titre,
            est_public=est_public,
            uploaded_by=user
        )
        HistoriqueFormation.objects.create(
            formation=self,
            champ_modifie="document",
            nouvelle_valeur=titre,
            commentaire=f"Document ajouté : {titre}",
            created_by=user
        )
        return document

    def add_evenement(self, type_evenement, event_date, details=None, description_autre=None, user=None):
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
        self.nombre_evenements = F('nombre_evenements') + 1
        self.save(update_fields=['nombre_evenements'])
        self.refresh_from_db(fields=['nombre_evenements'])

        HistoriqueFormation.objects.create(
            formation=self,
            champ_modifie="evenement",
            nouvelle_valeur=f"{type_evenement} le {event_date}",
            commentaire="Ajout d’un événement",
            created_by=user
        )

        return evenement

    def get_partenaires(self):
        return self.partenaires.all().prefetch_related()

    def get_commentaires(self):
        return self.commentaires.select_related("created_by").order_by('-created_at')

    def get_evenements(self):
        return self.evenements.select_related("created_by").order_by('-event_date')

    def get_documents(self):
        return self.documents.select_related("uploaded_by").all()

    def get_saturation_moyenne_commentaires(self):
        saturations = self.commentaires.exclude(saturation__isnull=True).values_list('saturation', flat=True)
        return round(sum(saturations) / len(saturations), 2) if saturations else None

    def get_status_color(self):
        return self.statut.couleur if self.statut.couleur else get_default_color(self.statut.nom)

    class Meta:
        verbose_name = "Formation"
        verbose_name_plural = "Formations"
        ordering = ['-start_date', 'nom']
        indexes = [
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
            models.Index(fields=['nom']),
            models.Index(fields=['statut']),
            models.Index(fields=['type_offre']),
            models.Index(fields=['convocation_envoie']),
            models.Index(fields=['centre']),
            models.Index(fields=['start_date', 'end_date']),  # ✅ ajouté
        ]


from django.db import models
from django.urls import reverse
from .base import BaseModel
import logging
logger = logging.getLogger("application.historiqueformation")

class HistoriqueFormation(BaseModel):
    """
    🕓 Historique de modification d'une formation.

    Ce modèle trace tous les changements appliqués à une formation, champ par champ,
    avec la date, l'utilisateur et un commentaire facultatif.
    """

    formation = models.ForeignKey(
        'Formation',
        on_delete=models.CASCADE,
        related_name="historiques",
        verbose_name="Formation concernée",
        help_text="Formation à laquelle ce changement est associé"
    )

    action = models.CharField(
        max_length=100,
        default='modification',
        verbose_name="Type d'action",
        help_text="Nature de l'action réalisée (ex : modification, ajout)"
    )

    champ_modifie = models.CharField(
        max_length=100,
        verbose_name="Champ modifié",
        help_text="Nom du champ ayant été modifié"
    )

    ancienne_valeur = models.TextField(
        null=True,
        blank=True,
        verbose_name="Ancienne valeur",
        help_text="Valeur avant la modification"
    )

    nouvelle_valeur = models.TextField(
        null=True,
        blank=True,
        verbose_name="Nouvelle valeur",
        help_text="Valeur après la modification"
    )

    commentaire = models.TextField(
        null=True,
        blank=True,
        verbose_name="Commentaire de modification",
        help_text="Commentaire explicatif (facultatif)"
    )

    details = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Détails supplémentaires",
        help_text="Données contextuelles (ex : ID utilisateur, origine, etc.)"
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

    def save(self, *args, **kwargs):
        """
        Sauvegarde l'entrée d'historique de formation dans une transaction atomique.

        Cette méthode surcharge `save()` pour garantir que chaque création ou mise à jour
        d'une instance de `HistoriqueFormation` est encapsulée dans une transaction.
        Cela assure l'intégrité des données en cas d'erreur pendant l'opération.

        Elle enregistre également un message dans les logs applicatifs pour suivre les modifications.

        Args:
            *args: Arguments positionnels transmis à `super().save()`.
            **kwargs: Arguments nommés transmis à `super().save()`.

        Returns:
            None
        """
        with transaction.atomic():
            super().save(*args, **kwargs)
        logger.info(f"[Historique] {self}")


    def get_absolute_url(self):
        """
        🔗 URL vers la page de détail de cette entrée d’historique.
        """
        return reverse("historiqueformation-detail", kwargs={"pk": self.pk})

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
            "created_at": self.created_at.strftime('%Y-%m-%d %H:%M'),
            "utilisateur": self.utilisateur_nom,
        }

    @property
    def utilisateur_nom(self):
        """
        👤 Nom de l'utilisateur ayant réalisé la modification.
        """
        if self.created_by:
            return f"{self.created_by.first_name} {self.created_by.last_name}".strip() or self.created_by.username
        return "Inconnu"
    


