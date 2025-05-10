from django.test import TestCase
from django.core.exceptions import ValidationError
from ...models.types_offre import TypeOffre
from .setup_base_tests import BaseModelTestSetupMixin


class TypeOffreModelTest(BaseModelTestSetupMixin, TestCase):
    """🧪 Tests unitaires pour le modèle TypeOffre"""

    def test_create_valid_standard_type(self):
        to = TypeOffre.objects.create(nom=TypeOffre.CRIF, created_by=self.user)
        self.assertEqual(to.nom, TypeOffre.CRIF)
        self.assertEqual(to.__str__(), "CRIF")

    def test_autre_requires_description(self):
        to = TypeOffre(nom=TypeOffre.AUTRE)
        with self.assertRaises(ValidationError):
            to.full_clean()

    def test_autre_uniqueness_constraint(self):
        TypeOffre.objects.create(nom=TypeOffre.AUTRE, autre="Stage renforcé", created_by=self.user)
        with self.assertRaises(ValidationError):
            TypeOffre(nom=TypeOffre.AUTRE, autre="Stage renforcé").full_clean()

    def test_color_is_validated(self):
        to = TypeOffre(nom=TypeOffre.CRIF, couleur="mauve")
        with self.assertRaises(ValidationError):
            to.full_clean()

    def test_assign_default_color_if_none(self):
        to = TypeOffre.objects.create(nom=TypeOffre.POEC, created_by=self.user)
        self.assertEqual(to.couleur, TypeOffre.COULEURS_PAR_DEFAUT[TypeOffre.POEC])

    def test_calculer_couleur_texte_for_light_and_dark(self):
        to_light = TypeOffre(nom=TypeOffre.CRIF, couleur="#FFFFFF")
        self.assertEqual(to_light.calculer_couleur_texte(), "#000000")
        to_dark = TypeOffre(nom=TypeOffre.CRIF, couleur="#000000")
        self.assertEqual(to_dark.calculer_couleur_texte(), "#FFFFFF")

    def test_get_badge_html_is_valid(self):
        to = TypeOffre.objects.create(nom=TypeOffre.TOSA, created_by=self.user)
        html = to.get_badge_html()
        self.assertIn("span", html)
        self.assertIn(to.__str__(), html)

    def test_to_serializable_dict_contains_expected_keys(self):
        to = TypeOffre.objects.create(nom=TypeOffre.CRIF, created_by=self.user)
        data = to.to_serializable_dict()
        self.assertIn("libelle", data)
        self.assertIn("badge_html", data)
        self.assertIn("formations_count", data)

    def test_to_csv_row_format(self):
        to = TypeOffre.objects.create(nom=TypeOffre.CRIF, created_by=self.user)
        row = to.to_csv_row()
        self.assertEqual(row[2], TypeOffre.CRIF)
        self.assertIn(to.couleur, row)

    def test_repr_for_standard_and_autre(self):
        std = TypeOffre(nom=TypeOffre.POEI)
        self.assertIn("poei", repr(std))
        perso = TypeOffre(nom=TypeOffre.AUTRE, autre="Bilan perso")
        self.assertIn("Bilan perso", str(perso))

    def test_is_personnalise_returns_expected(self):
        self.assertTrue(TypeOffre(nom=TypeOffre.AUTRE).is_personnalise())
        self.assertFalse(TypeOffre(nom=TypeOffre.CRIF).is_personnalise())

    def test_invalidate_caches_does_not_error(self):
        to = TypeOffre.objects.create(nom=TypeOffre.POEC, created_by=self.user)
        to.invalidate_caches()  # ne lève pas d'erreur

    def test_save_with_skip_validation_ignores_validation(self):
        to = TypeOffre(nom=TypeOffre.AUTRE)  # pas de champ 'autre' renseigné
        try:
            to.save(skip_validation=True, user=self.user)
        except ValidationError:
            self.fail("skip_validation=True devrait désactiver la validation")

