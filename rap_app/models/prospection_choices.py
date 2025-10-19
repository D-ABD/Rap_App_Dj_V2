from django.utils.translation import gettext_lazy as _

class ProspectionChoices:
    # ────────────────────────────────
    # Statuts (cycle de vie métier)
    # ────────────────────────────────
    STATUT_A_FAIRE = 'a_faire'
    STATUT_EN_COURS = 'en_cours'
    STATUT_A_RELANCER = 'a_relancer'
    STATUT_ACCEPTEE = 'acceptee'
    STATUT_REFUSEE = 'refusee'
    STATUT_ANNULEE = 'annulee'
    STATUT_NON_RENSEIGNE = 'non_renseigne'

    PROSPECTION_STATUS_CHOICES = [
        (STATUT_A_FAIRE,      _('À faire')),
        (STATUT_EN_COURS,     _('En cours')),
        (STATUT_A_RELANCER,   _('À relancer')),
        (STATUT_ACCEPTEE,     _('Acceptée')),
        (STATUT_REFUSEE,      _('Refusée')),
        (STATUT_ANNULEE,      _('Annulée')),
        (STATUT_NON_RENSEIGNE,_('Non renseigné')),
    ]

    # ────────────────────────────────
    # Objectifs
    # ────────────────────────────────
    OBJECTIF_PRISE_CONTACT = 'prise_contact'
    OBJECTIF_RENDEZ_VOUS = 'rendez_vous'
    OBJECTIF_PRESENTATION = 'presentation_offre'
    OBJECTIF_CONTRAT = 'contrat'
    OBJECTIF_PARTENARIAT = 'partenariat'
    OBJECTIF_AUTRE = 'autre'

    PROSPECTION_OBJECTIF_CHOICES = [
        (OBJECTIF_PRISE_CONTACT, _('Prise de contact')),
        (OBJECTIF_RENDEZ_VOUS, _('Obtenir un rendez-vous')),
        (OBJECTIF_PRESENTATION, _("Présentation d'une offre")),
        (OBJECTIF_CONTRAT, _('Signer un contrat')),
        (OBJECTIF_PARTENARIAT, _('Établir un partenariat')),
        (OBJECTIF_AUTRE, _('Autre')),
    ]

    # ────────────────────────────────
    # Motifs
    # ────────────────────────────────
    MOTIF_POEI = 'POEI'
    MOTIF_APPRENTISSAGE = 'apprentissage'
    MOTIF_VAE = 'VAE'
    MOTIF_PARTENARIAT = 'partenariat'
    MOTIF_AUTRE = 'autre'

    PROSPECTION_MOTIF_CHOICES = [
        (MOTIF_POEI, _('POEI')),
        (MOTIF_APPRENTISSAGE, _('Apprentissage')),
        (MOTIF_VAE, _('VAE')),
        (MOTIF_PARTENARIAT, _('Établir un partenariat')),
        (MOTIF_AUTRE, _('Autre')),
    ]

    # ────────────────────────────────
    # Moyens de contact
    # ────────────────────────────────
    MOYEN_EMAIL = 'email'
    MOYEN_TELEPHONE = 'telephone'
    MOYEN_VISITE = 'visite'
    MOYEN_RESEAUX = 'reseaux'

    MOYEN_CONTACT_CHOICES = [
        (MOYEN_EMAIL, _('Email')),
        (MOYEN_TELEPHONE, _('Téléphone')),
        (MOYEN_VISITE, _('Visite')),
        (MOYEN_RESEAUX, _('Réseaux sociaux')),
    ]

    # ────────────────────────────────
    # Types de prospection
    # ────────────────────────────────
    TYPE_NOUVEAU_PROSPECT = 'nouveau_prospect'
    TYPE_PREMIER_CONTACT = 'premier_contact'
    TYPE_RELANCE = 'relance'
    TYPE_REPRISE_CONTACT = 'reprise_contact'
    TYPE_SUIVI = 'suivi'
    TYPE_RAPPEL_PROGRAMME = 'rappel_programme'
    TYPE_FIDELISATION = 'fidelisation'
    TYPE_AUTRE = 'autre'

    TYPE_PROSPECTION_CHOICES = [
        (TYPE_NOUVEAU_PROSPECT, _("Nouveau prospect")),
        (TYPE_PREMIER_CONTACT, _("Premier contact")),
        (TYPE_RELANCE, _("Relance")),
        (TYPE_REPRISE_CONTACT, _("Reprise de contact")),
        (TYPE_SUIVI, _("Suivi en cours")),
        (TYPE_RAPPEL_PROGRAMME, _("Rappel programmé")),
        (TYPE_FIDELISATION, _("Fidélisation")),
        (TYPE_AUTRE, _("Autre")),
    ]

    # ────────────────────────────────
    # Helpers
    # ────────────────────────────────
    @classmethod
    def get_statut_labels(cls):
        return dict(cls.PROSPECTION_STATUS_CHOICES)

    @classmethod
    def get_objectifs_labels(cls):
        return dict(cls.PROSPECTION_OBJECTIF_CHOICES)

    @staticmethod
    def get_statut_choices():
        return [{"value": val, "label": label} for val, label in ProspectionChoices.PROSPECTION_STATUS_CHOICES]

    @staticmethod
    def get_objectif_choices():
        return [{"value": val, "label": label} for val, label in ProspectionChoices.PROSPECTION_OBJECTIF_CHOICES]

    @staticmethod
    def get_motif_choices():
        return [{"value": val, "label": label} for val, label in ProspectionChoices.PROSPECTION_MOTIF_CHOICES]

    @staticmethod
    def get_type_choices():
        return [{"value": val, "label": label} for val, label in ProspectionChoices.TYPE_PROSPECTION_CHOICES]

    @staticmethod
    def get_moyen_contact_choices():
        return [{"value": val, "label": label} for val, label in ProspectionChoices.MOYEN_CONTACT_CHOICES]
