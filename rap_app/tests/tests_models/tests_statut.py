from django.core.exceptions import ValidationError
from django.test import TestCase

from ...models.centres import Centre
from ...models.types_offre import TypeOffre

from ...models.formations import Formation
from ...models.statut import Statut, get_default_color, calculer_couleur_texte
from .setup_base_tests import BaseModelTestSetupMixin


class StatutModelTest(BaseModelTestSetupMixin, TestCase):
    """🧪 Tests unitaires pour le modèle Statut."""

    def setUp(self):
        super().setUp()

        # Dépendances pour la formation
        self.centre = self.create_instance(Centre, nom="Centre Test")
        self.type_offre = self.create_instance(TypeOffre, nom=TypeOffre.CRIF)
        self.statut = self.create_instance(Statut, nom=Statut.NON_DEFINI)

        # Formation liée
        self.formation = self.create_instance(
            Formation,
            nom="Formation pour document",
            centre=self.centre,
            type_offre=self.type_offre,
            statut=self.statut,
        )


    def test_create_valid_statut(self):
        statut = Statut.objects.create(nom=Statut.PLEINE, created_by=self.user)
        self.assertEqual(statut.nom, Statut.PLEINE)
        self.assertTrue(statut.couleur.startswith("#"))

    def test_default_color_is_applied(self):
        statut = Statut(nom=Statut.FORMATION_EN_COURS, created_by=self.user)
        statut.save()
        self.assertEqual(statut.couleur, get_default_color(Statut.FORMATION_EN_COURS))

    def test_autre_requires_description(self):
        statut = Statut(nom=Statut.AUTRE)
        with self.assertRaises(ValidationError) as ctx:
            statut.full_clean()
        self.assertIn("description personnalisée", str(ctx.exception))

    def test_invalid_color_format_raises(self):
        statut = Statut(nom=Statut.NON_DEFINI, couleur="bleu")
        with self.assertRaises(ValidationError):
            statut.full_clean()

    def test_get_nom_display_returns_description_for_autre(self):
        statut = Statut(nom=Statut.AUTRE, description_autre="Statut personnalisé")
        self.assertEqual(statut.get_nom_display(), "Statut personnalisé")

    def test_get_nom_display_for_standard(self):
        statut = Statut(nom=Statut.NON_DEFINI)
        self.assertEqual(statut.get_nom_display(), "Non défini")

    def test_get_badge_html_is_valid(self):
        statut = Statut(nom=Statut.NON_DEFINI)
        statut.save()
        html = statut.get_badge_html()
        self.assertIn("span", html)
        self.assertIn(statut.get_nom_display(), html)

    def test_to_csv_row_contains_expected_fields(self):
        statut = Statut.objects.create(nom=Statut.NON_DEFINI, created_by=self.user)
        row = statut.to_csv_row()
        self.assertEqual(row[2], Statut.NON_DEFINI)

    def test_calculer_couleur_texte_logic(self):
        noir = calculer_couleur_texte("#FFFFFF")
        blanc = calculer_couleur_texte("#000000")
        self.assertEqual(noir, "#000000")
        self.assertEqual(blanc, "#FFFFFF")

    def test_to_serializable_dict_contains_keys(self):
        statut = Statut.objects.create(nom=Statut.FORMATION_EN_COURS, created_by=self.user)
        data = statut.to_serializable_dict()
        self.assertIn("badge_html", data)
        self.assertIn("libelle", data)

    def test_str_and_repr_methods(self):
        statut = Statut.objects.create(nom=Statut.PLEINE, created_by=self.user)
        self.assertIn("Pleine", str(statut))
        self.assertIn("Statut", repr(statut))

    def test_invalidate_caches_executes_without_error(self):
        statut = Statut.objects.create(nom=Statut.NON_DEFINI, created_by=self.user)
        try:
            statut.invalidate_caches()  # Doit passer sans erreur
        except Exception as e:
            self.fail(f"invalidate_caches a levé une exception : {e}")

    def test_save_with_skip_validation(self):
        statut = Statut(
            nom=Statut.AUTRE, 
            description_autre="",  # Invalide normalement
            created_by=self.user
        )
        try:
            statut.save(skip_validation=True)
        except ValidationError:
            self.fail("Le paramètre skip_validation=True aurait dû désactiver la validation")


    def test_created_by_fallback_is_system(self):
        statut = Statut(nom=Statut.NON_DEFINI)
        statut.save(skip_validation=True)  # Pas de self.user transmis
        self.assertIsNone(statut.created_by)
        row = statut.to_csv_row()
        self.assertEqual(row[-1], "Système")  # Vérifie fallback CSV
