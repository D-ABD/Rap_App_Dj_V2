from django.db import models
from django.utils import timezone


class CerfaContrat(models.Model):
    """
    Version complète du modèle CERFA Contrat sans clé étrangère.
    Tous les champs du CERFA 10103*14 sont présents pour permettre le remplissage total du PDF.
    """

    pdf_fichier = models.FileField(
        upload_to="cerfas/",
        blank=True,
        null=True,
        verbose_name="Fichier PDF généré",
    )

    auto_generated = models.BooleanField(default=False)

    # ───────────── EMPLOYEUR ─────────────
    employeur_prive = models.BooleanField(default=True)
    employeur_public = models.BooleanField(default=False)
    employeur_nom = models.CharField(max_length=255, blank=True, null=True)
    employeur_adresse_numero = models.CharField(max_length=20, blank=True, null=True)
    employeur_adresse_voie = models.CharField(max_length=255, blank=True, null=True)
    employeur_adresse_complement = models.CharField(max_length=255, blank=True, null=True)
    employeur_code_postal = models.CharField(max_length=10, blank=True, null=True)
    employeur_commune = models.CharField(max_length=255, blank=True, null=True)
    employeur_telephone = models.CharField(max_length=50, blank=True, null=True)
    employeur_email = models.EmailField(blank=True, null=True)
    employeur_siret = models.CharField(max_length=20, blank=True, null=True)
    employeur_type = models.CharField(max_length=100, blank=True, null=True)
    employeur_specifique = models.CharField(max_length=100, blank=True, null=True)
    employeur_code_ape = models.CharField(max_length=10, blank=True, null=True)
    employeur_effectif = models.PositiveIntegerField(blank=True, null=True)
    employeur_code_idcc = models.CharField(max_length=20, blank=True, null=True)
    employeur_regime_assurance_chomage = models.BooleanField(default=False)

    # ───────────── MAÎTRES D’APPRENTISSAGE ─────────────
    maitre1_nom = models.CharField(max_length=255, blank=True, null=True)
    maitre1_prenom = models.CharField(max_length=255, blank=True, null=True)
    maitre1_date_naissance = models.DateField(blank=True, null=True)
    maitre1_email = models.EmailField(blank=True, null=True)
    maitre1_emploi = models.CharField(max_length=255, blank=True, null=True)
    maitre1_diplome = models.CharField(max_length=255, blank=True, null=True)
    maitre1_niveau_diplome = models.CharField(max_length=255, blank=True, null=True)

    maitre2_nom = models.CharField(max_length=255, blank=True, null=True)
    maitre2_prenom = models.CharField(max_length=255, blank=True, null=True)
    maitre2_date_naissance = models.DateField(blank=True, null=True)
    maitre2_email = models.EmailField(blank=True, null=True)
    maitre2_emploi = models.CharField(max_length=255, blank=True, null=True)
    maitre2_diplome = models.CharField(max_length=255, blank=True, null=True)
    maitre2_niveau_diplome = models.CharField(max_length=255, blank=True, null=True)
    maitre_eligible = models.BooleanField(default=True)

    # ───────────── APPRENTI ─────────────
    apprenti_nom_naissance = models.CharField(max_length=255, blank=True, null=True)
    apprenti_nom_usage = models.CharField(max_length=255, blank=True, null=True)
    apprenti_prenom = models.CharField(max_length=255, blank=True, null=True)
    apprenti_nir = models.CharField(max_length=15, blank=True, null=True)
    apprenti_numero = models.CharField(max_length=20, blank=True, null=True)
    apprenti_voie = models.CharField(max_length=255, blank=True, null=True)
    apprenti_complement = models.CharField(max_length=255, blank=True, null=True)
    apprenti_code_postal = models.CharField(max_length=10, blank=True, null=True)
    apprenti_commune = models.CharField(max_length=255, blank=True, null=True)
    apprenti_telephone = models.CharField(max_length=50, blank=True, null=True)
    apprenti_email = models.EmailField(blank=True, null=True)
    apprenti_date_naissance = models.DateField(blank=True, null=True)
    apprenti_sexe = models.CharField(
        max_length=1, choices=[("M", "Masculin"), ("F", "Féminin")], blank=True, null=True
    )
    apprenti_departement_naissance = models.CharField(max_length=50, blank=True, null=True)
    apprenti_commune_naissance = models.CharField(max_length=255, blank=True, null=True)
    apprenti_nationalite = models.CharField(max_length=100, blank=True, null=True)
    apprenti_regime_social = models.CharField(max_length=100, blank=True, null=True)
    apprenti_sportif_haut_niveau = models.BooleanField(default=False)
    apprenti_rqth = models.BooleanField(default=False)
    apprenti_droits_rqth = models.BooleanField(default=False)
    apprenti_equivalence_jeunes = models.BooleanField(default=False)
    apprenti_extension_boe = models.BooleanField(default=False)
    apprenti_projet_entreprise = models.BooleanField(default=False)
    apprenti_situation_avant = models.CharField(max_length=255, blank=True, null=True)
    apprenti_dernier_diplome_prepare = models.CharField(max_length=255, blank=True, null=True)
    apprenti_derniere_annee_suivie = models.CharField(max_length=100, blank=True, null=True)
    apprenti_intitule_dernier_diplome = models.CharField(max_length=255, blank=True, null=True)
    apprenti_plus_haut_diplome = models.CharField(max_length=255, blank=True, null=True)

    # Représentant légal
    representant_nom = models.CharField(max_length=255, blank=True, null=True)
    representant_lien = models.CharField(max_length=100, blank=True, null=True)
    representant_adresse_voie = models.CharField(max_length=255, blank=True, null=True)
    representant_code_postal = models.CharField(max_length=10, blank=True, null=True)
    representant_commune = models.CharField(max_length=255, blank=True, null=True)
    representant_email = models.EmailField(blank=True, null=True)

    # ───────────── FORMATION / CFA ─────────────
    cfa_denomination = models.CharField(max_length=255, blank=True, null=True)
    cfa_uai = models.CharField(max_length=50, blank=True, null=True)
    cfa_siret = models.CharField(max_length=20, blank=True, null=True)
    cfa_commune = models.CharField(max_length=255, blank=True, null=True)
    diplome_vise = models.CharField(max_length=255, blank=True, null=True)
    diplome_intitule = models.CharField(max_length=255, blank=True, null=True)
    code_diplome = models.CharField(max_length=50, blank=True, null=True)
    code_rncp = models.CharField(max_length=50, blank=True, null=True)
    formation_debut = models.DateField(blank=True, null=True)
    formation_fin = models.DateField(blank=True, null=True)
    formation_duree_heures = models.PositiveIntegerField(blank=True, null=True)
    formation_distance_heures = models.PositiveIntegerField(blank=True, null=True)
    formation_lieu_denomination = models.CharField(max_length=255, blank=True, null=True)
    formation_lieu_uai = models.CharField(max_length=50, blank=True, null=True)
    formation_lieu_siret = models.CharField(max_length=20, blank=True, null=True)
    formation_lieu_voie = models.CharField(max_length=255, blank=True, null=True)
    formation_lieu_code_postal = models.CharField(max_length=10, blank=True, null=True)
    formation_lieu_commune = models.CharField(max_length=255, blank=True, null=True)

    # ───────────── CONTRAT ─────────────
    type_contrat = models.CharField(max_length=255, blank=True, null=True)
    date_conclusion = models.DateField(blank=True, null=True)
    date_debut_execution = models.DateField(blank=True, null=True)
    date_fin_contrat = models.DateField(blank=True, null=True)
    duree_hebdo_heures = models.PositiveIntegerField(blank=True, null=True)
    salaire_brut_mensuel = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    caisse_retraite = models.CharField(max_length=255, blank=True, null=True)
    avantage_nourriture = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)
    avantage_logement = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)
    avantage_autre = models.CharField(max_length=255, blank=True, null=True)

    # ───────────── SIGNATURES ─────────────
    lieu_signature = models.CharField(max_length=255, blank=True, null=True)
    date_signature_apprenti = models.DateField(blank=True, null=True)
    date_signature_employeur = models.DateField(blank=True, null=True)
    signature_apprenti = models.BooleanField(default=False)
    signature_employeur = models.BooleanField(default=False)

    # ───────────── MÉTADONNÉES ─────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "CERFA Contrat complet"
        ordering = ["-created_at"]

    def __str__(self):
        return f"CERFA {self.id or '?'} - {self.apprenti_nom_naissance or 'Apprenti'}"


class CerfaRemuneration(models.Model):
    """
    Période de rémunération (simplifiée, sans ForeignKey)
    """
    contrat_id = models.IntegerField(blank=True, null=True, help_text="ID du contrat (rempli manuellement si besoin)")
    annee = models.PositiveSmallIntegerField(choices=[(1, "1ère année"), (2, "2e année"), (3, "3e année")])
    date_debut = models.DateField(blank=True, null=True)
    date_fin = models.DateField(blank=True, null=True)
    pourcentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    reference = models.CharField(max_length=10, choices=[("SMIC", "SMIC"), ("SMC", "SMC")], default="SMIC")
    montant_mensuel_estime = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)

    class Meta:
        verbose_name = "Rémunération CERFA"
        ordering = ["annee", "date_debut"]

    def __str__(self):
        return f"{self.annee}ᵉ année ({self.pourcentage or '?'}% du {self.reference})"
  