import logging
import re
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.utils.html import format_html
from django.urls import reverse
from .base import BaseModel

# Configuration du logger
logger = logging.getLogger("application.typeoffre")

# ----------------------------------------------------
# Signaux déplacés dans un fichier signals/
# ----------------------------------------------------


class TypeOffre(BaseModel):
    """
    📋 Modèle représentant les types d'offres de formation.

    Ce modèle définit les différents types d'offres disponibles dans l'application, 
    comme CRIF, Alternance, POEC, POEI, etc. Il permet également d'ajouter un type personnalisé 
    via l'option "Autre".

    Attributes:
        nom: Type d'offre sélectionné parmi les choix prédéfinis
        autre: Description personnalisée si le type est "Autre"
        couleur: Code couleur hexadécimal pour l'affichage visuel
        created_at: Date de création (de BaseModel)
        updated_at: Date de dernière modification (de BaseModel)
    
    ✅ Utilisation principale :
    - Associer un type d'offre à une formation.
    - Filtrer les formations par type d'offre.
    - Permettre l'ajout d'un type personnalisé si besoin.
    - Sérialisation facilité pour l'API REST.
    """

    # Constantes pour les choix de types d'offre
    CRIF = 'crif'
    ALTERNANCE = 'alternance'
    POEC = 'poec'
    POEI = 'poei'
    TOSA = 'tosa'
    AUTRE = 'autre'
    NON_DEFINI = 'non_defini'
    
    TYPE_OFFRE_CHOICES = [
        (CRIF, 'CRIF'),
        (ALTERNANCE, 'Alternance'),
        (POEC, 'POEC'),
        (POEI, 'POEI'),
        (TOSA, 'TOSA'),
        (AUTRE, 'Autre'),
        (NON_DEFINI, 'Non défini'),
    ]
    
    # Mapping des couleurs par défaut pour chaque type d'offre
    COULEURS_PAR_DEFAUT = {
        CRIF: "#D735B4",        # 🔵 Bleu (CRIF)
        ALTERNANCE: "#063c68",  # 🟢 Vert (Alternance)
        POEC: "#260a5b",        # 🟣 Violet (POEC)
        POEI: "#0b4f04",        # 🟠 Orange (POEI)
        TOSA: "#323435",         # ⚙️ Gris (TOSA)
        AUTRE: "#ff6207",        # 🟡 Jaune (Autre)
        NON_DEFINI: "#000000",   # ⚫ Noir (Non défini)
    }
    
    nom = models.CharField(
        max_length=100, 
        choices=TYPE_OFFRE_CHOICES, 
        default=NON_DEFINI, 
        verbose_name="Type d'offre",
        help_text="Sélectionnez le type d'offre de formation parmi les choix prédéfinis"
    )
    
    autre = models.CharField(
        max_length=255, 
        blank=True,
        verbose_name="Autre (personnalisé)",
        help_text="Si vous avez choisi 'Autre', précisez le type d'offre personnalisé"
    )
    
    couleur = models.CharField(
        max_length=7,
        blank=True,
        null=True,
        verbose_name="Couleur associée (hexadécimal)",
        help_text="Code couleur hexadécimal (ex: #FF5733) pour l'affichage visuel"
    )


    def to_csv_row(self) -> list[str]:
        """
        📤 Convertit le type d'offre en ligne pour export CSV.

        Returns:
            list: Valeurs ordonnées correspondant aux en-têtes CSV
        """
        return [
            str(self.pk),
            self.get_nom_display(),
            self.nom,
            self.autre or '',
            self.couleur,
            str(self.get_formations_count()),
            self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else '',
            self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else '',
            self.created_by.username if self.created_by else 'Système',
        ]

    @classmethod
    def get_csv_fields(cls) -> list[str]:
        """
        🗂️ Liste des champs exportables.

        Returns:
            list: Noms de champs (correspondant aux colonnes)
        """
        return ['id', 'libelle_affiche', 'nom_technique', 'autre', 'couleur', 'nb_formations', 'created_at', 'updated_at', 'created_by']

    @classmethod
    def get_csv_headers(cls) -> list[str]:
        """
        🏷️ En-têtes lisibles pour l’export CSV.

        Returns:
            list: En-têtes pour la première ligne du CSV
        """
        return ['ID', 'Libellé affiché', 'Nom technique', 'Autre (perso)', 'Couleur', 'Nb formations', 'Créé le', 'Modifié le', 'Créé par']

    def clean(self):
        """
        🔍 Validation personnalisée des données avant sauvegarde.
        
        Vérifications:
        - Si le type d'offre est 'Autre', alors `autre` doit être rempli
        - Format valide pour le code couleur hexadécimal
        - Unicité du champ 'autre' pour les types personnalisés
        
        Raises:
            ValidationError: Si les conditions de validation ne sont pas remplies
        """
        super().clean()
        
        # Validation du type "Autre"
        if self.nom == self.AUTRE and not self.autre:
            raise ValidationError({
                'autre': "Le champ 'autre' doit être renseigné lorsque le type d'offre est 'Autre'."
            })
        
        # Validation du format du code couleur
        if self.couleur:
            # Vérification du format hexadécimal (#RRGGBB ou #RGB)
            if not re.match(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', self.couleur):
                raise ValidationError({
                    'couleur': "Le format de couleur doit être un code hexadécimal valide (ex: #FF5733)."
                })
        
        # Vérification de l'unicité du champ 'autre' pour les types personnalisés
        if self.nom == self.AUTRE and self.autre:
            # Vérifier si un autre objet avec le même 'autre' existe déjà
            # Exclure l'objet actuel si on est en train de le modifier
            queryset = TypeOffre.objects.filter(nom=self.AUTRE, autre=self.autre)
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)
            
            if queryset.exists():
                raise ValidationError({
                    'autre': f"Un type d'offre personnalisé avec le nom '{self.autre}' existe déjà."
                })

    def save(self, *args, **kwargs):
        """
        💾 Sauvegarde personnalisée du modèle TypeOffre.

        Gère :
        - La validation conditionnelle via `skip_validation`
        - L’attribution automatique d’une couleur par défaut
        - La journalisation détaillée des changements
        - La compatibilité avec le champ `user` de BaseModel

        Args:
            *args: Arguments positionnels transmis à `super().save()`
            **kwargs:
                - user (User): Utilisateur à l’origine de la modification
                - skip_validation (bool): Si True, désactive la validation (`.full_clean()`)
        """
        is_new = self.pk is None
        user = kwargs.pop("user", None)
        skip_validation = kwargs.pop("skip_validation", False)

        if user:
            self._user = user  # transmis à BaseModel pour journalisation

        # Nettoyage des champs
        if self.autre:
            self.autre = self.autre.strip()

        if not self.couleur:
            self.couleur = "#6c757d"
        else:
            self.couleur = self.couleur.lower()

        # Affecter une couleur par défaut si nécessaire
        self.assign_default_color()

        # Appliquer la validation uniquement si non désactivée
        if not skip_validation:
            self.full_clean()

        with transaction.atomic():
            old_instance = None
            if not is_new:
                try:
                    old_instance = TypeOffre.objects.get(pk=self.pk)
                except TypeOffre.DoesNotExist:
                    pass

            # Appel à BaseModel.save() avec les bons kwargs
            super().save(*args, user=user, skip_validation=skip_validation, **kwargs)

            # Logging
            if is_new:
                logger.info(f"🆕 Création du type d'offre : {self}")
            elif old_instance:
                modifications = []
                if old_instance.nom != self.nom:
                    modifications.append(f"nom: {old_instance.nom} → {self.nom}")
                if old_instance.autre != self.autre:
                    modifications.append(f"autre: {old_instance.autre} → {self.autre}")
                if old_instance.couleur != self.couleur:
                    modifications.append(f"couleur: {old_instance.couleur} → {self.couleur}")

                if modifications:
                    logger.info(f"✏️ Modification du type d'offre #{self.pk} : " + ", ".join(modifications))

    def assign_default_color(self):
        """
        🎨 Assigne une couleur par défaut selon le type d'offre si aucune 
        couleur personnalisée n'est définie.
        """
        # On affecte seulement si aucune couleur personnalisée ou si c'est la couleur grise par défaut
        if not self.couleur or self.couleur == "#6c757d":
            self.couleur = self.COULEURS_PAR_DEFAUT.get(self.nom, "#6c757d")
            logger.debug(f"Couleur par défaut assignée au type d'offre {self}: {self.couleur}")

    def __str__(self):
        """
        🔁 Représentation textuelle du modèle dans l'admin Django et les logs.

        Returns:
            str: Nom personnalisé si le type est "Autre", sinon le nom standard ou clé brute
        """
        if self.nom == self.AUTRE and self.autre:
            return self.autre
        return dict(self.TYPE_OFFRE_CHOICES).get(self.nom, self.nom)

    
    def __repr__(self):
        """
        📝 Représentation technique pour le débogage.
        
        Returns:
            str: Format technique détaillé
        """
        return f"<TypeOffre(id={self.pk}, nom='{self.nom}', autre='{self.autre if self.nom == self.AUTRE else ''}')>"
    
    
    def is_personnalise(self):
        """
        🔍 Vérifie si le type d'offre est personnalisé (Autre).
        
        Returns:
            bool: True si le type est "Autre", False sinon
        """
        return self.nom == self.AUTRE
    
    def calculer_couleur_texte(self):
        """
        🎨 Détermine la couleur de texte adaptée (blanc ou noir) en fonction de la couleur de fond.
        
        Utilise une heuristique simple: les couleurs claires (jaune) ont un texte noir,
        les autres ont un texte blanc pour assurer la lisibilité.
        
        Returns:
            str: '#000000' pour les fonds clairs, '#FFFFFF' pour les fonds foncés
        """
        try:
            # Convertir le code hexadécimal en valeurs RGB
            hex_color = self.couleur.lstrip('#')
            if len(hex_color) == 3:
                # Convertir les formats courts (#RGB) en format long (#RRGGBB)
                hex_color = ''.join([c*2 for c in hex_color])
            
            r, g, b = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
            
            # Calculer la luminosité (formule standard)
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            
            # Si la luminosité est supérieure à 0.5, la couleur est considérée comme claire
            if luminance > 0.5:
                return '#000000'  # Texte noir pour les fonds clairs
            return '#FFFFFF'  # Texte blanc pour les fonds foncés
        except Exception as e:
            # En cas d'erreur, utiliser du texte blanc par défaut
            logger.warning(f"Erreur lors du calcul de la luminosité pour {self.couleur}: {str(e)}")
            return '#FFFFFF'
    
    def get_badge_html(self):
        """
        🏷️ Génère le HTML pour afficher un badge avec la couleur du type d'offre.
        
        Returns:
            SafeString: Code HTML formaté pour le badge
        """
        couleur_texte = self.calculer_couleur_texte()
        return format_html(
            '<span class="badge" style="background-color:{}; color:{}; padding: 3px 8px; border-radius: 5px;">{}</span>',
            self.couleur,
            couleur_texte,
            self.__str__()
        )
    
    def get_formations_count(self):
        """
        📊 Retourne le nombre de formations associées à ce type d'offre.
        
        Returns:
            int: Nombre de formations utilisant ce type d'offre
        """
        return self.formations.count()
    
    def to_serializable_dict(self, exclude=None):
        """
        📦 Retourne un dictionnaire sérialisable du type d'offre.
        
        Args:
            exclude (list[str], optional): Liste de champs à exclure
            
        Returns:
            dict: Données sérialisables du type d'offre
        """
        exclude = exclude or []
        data = super().to_serializable_dict(exclude)
        
        # Ajouter des données spécifiques au type d'offre
        data.update({
            'libelle': self.__str__(),
            'is_personnalise': self.is_personnalise(),
            'formations_count': self.get_formations_count(),
            'badge_html': self.get_badge_html(),
        })
        
        return data
    
    def invalidate_caches(self):
        """
        🔄 Invalide les caches associés à ce type d'offre.
        """
        super().invalidate_caches()
        
        # Invalider les caches spécifiques aux types d'offre
        from django.core.cache import cache
        cache_keys = [
            f"typeoffre_{self.pk}",
            f"typeoffre_liste",
            f"typeoffre_{self.nom}",
            f"formations_par_typeoffre_{self.pk}"
        ]
        
        for key in cache_keys:
            cache.delete(key)

    class Meta:
        verbose_name = "Type d'offre"
        verbose_name_plural = "Types d'offres"
        ordering = ['nom']
        constraints = [
            models.UniqueConstraint(
                fields=['autre'],
                name='unique_autre_non_null',
                condition=models.Q(nom='autre', autre__isnull=False)
            )
        ]
        # Ajout d'index pour optimiser les requêtes fréquentes
        indexes = [
            models.Index(fields=['nom'], name='typeoffre_nom_idx'),
            models.Index(fields=['autre'], name='typeoffre_autre_idx'),
        ]