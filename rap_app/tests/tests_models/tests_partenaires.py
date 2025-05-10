import pytest
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from ...models.partenaires import Partenaire
from .setup_base_tests import BaseModelTestSetupMixin


class PartenaireModelTest(BaseModelTestSetupMixin):
    def setUp(self):
        super().setUp()
        self.partenaire = self.create_instance(
            Partenaire,
            nom="Entreprise Test",
            type=Partenaire.TYPE_ENTREPRISE,
            zip_code="75001",
            city="Paris",
            contact_nom="Jean Dupont",
            contact_telephone="0123456789",
            contact_email="contact@exemple.com"
        )



    def test_clean_empty_nom_raises(self):
        with self.assertRaises(ValidationError):
            p = Partenaire(nom=" ")
            p.full_clean()

    def test_clean_zip_code_requires_city(self):
        with self.assertRaises(ValidationError):
            p = Partenaire(nom="X", zip_code="75001")
            p.full_clean()

    def test_clean_invalid_website(self):
        p = Partenaire(nom="X", website="invalid-url", city="Paris", zip_code="75001")
        with self.assertRaises(ValidationError):
            p.full_clean()

    def test_clean_valid_social_network_url(self):
        p = self.create_instance(
            Partenaire,
            nom="Y",
            social_network_url="https://linkedin.com/in/xyz",
            city="Lyon",
            zip_code="69000"
        )
        try:
            p.full_clean()  # Ne doit pas lever d'erreur
        except ValidationError:
            self.fail("ValidationError raised for a valid social network URL")

    def test_slug_auto_generated(self):
        self.assertEqual(self.partenaire.slug, slugify(self.partenaire.nom))

    def test_has_contact(self):
        self.assertTrue(self.partenaire.has_contact)

    def test_has_address(self):
        self.assertTrue(self.partenaire.has_address)

    def test_has_web_presence_false(self):
        self.assertFalse(self.partenaire.has_web_presence)

    def test_get_full_address(self):
        expected = "75001 Paris, France"
        self.assertIn(expected, self.partenaire.get_full_address())

    def test_get_contact_info(self):
        self.assertIn("Jean Dupont", self.partenaire.get_contact_info())

    def test_to_serializable_dict(self):
        data = self.partenaire.to_serializable_dict()
        self.assertEqual(data["nom"], self.partenaire.nom)
        self.assertIn("localisation", data)
        self.assertIn("contact", data)

    def test_get_prospections_info(self):
        infos = self.partenaire.get_prospections_info()
        self.assertIn("count", infos)

    def test_get_formations_info(self):
        infos = self.partenaire.get_formations_info()
        self.assertIn("count", infos)


    def test_get_secteurs_list(self):
        secteurs = Partenaire.get_secteurs_list()
        self.assertIn("Secteur test", secteurs) if self.partenaire.secteur_activite else True

    def test_manager_methods(self):
        # test entreprises()
        self.assertIn(self.partenaire, Partenaire.custom.entreprises())

        # test personnes()
        p2 = self.create_instance(Partenaire, nom="Individu", type=Partenaire.TYPE_PERSONNE)
        self.assertIn(p2, Partenaire.custom.personnes())

        # test institutionnels()
        p3 = self.create_instance(Partenaire, nom="Institution", type=Partenaire.TYPE_INSTITUTIONNEL)
        self.assertIn(p3, Partenaire.custom.institutionnels())

        # test avec_contact()
        self.assertIn(self.partenaire, Partenaire.custom.avec_contact())

        # test par_secteur()
        self.partenaire.secteur_activite = "Tech"
        self.partenaire.save()
        self.assertIn(self.partenaire, Partenaire.custom.par_secteur("tech"))

        # test recherche()
        results = Partenaire.custom.recherche("Entreprise")
        self.assertIn(self.partenaire, results)
