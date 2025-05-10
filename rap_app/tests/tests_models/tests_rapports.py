# tests/tests_models/test_rapport.py

from django.test import TestCase
from django.utils import timezone
from django.core.cache import cache
from django.core.exceptions import ValidationError
from datetime import timedelta

from ...models.partenaires import Partenaire
from ...models.prospection import Prospection, ProspectionChoices
from ...models.rapports import Rapport
from ...models.centres import Centre
from ...models.formations import Formation
from ...models.types_offre import TypeOffre
from ...models.statut import Statut
from .setup_base_tests import BaseModelTestSetupMixin


class RapportModelTest(BaseModelTestSetupMixin, TestCase):

    def setUp(self):
        super().setUp()

        self.date_debut = timezone.now().date()
        self.date_fin = self.date_debut + timedelta(days=1)

        self.centre = self.create_instance(Centre, nom="Centre Prospection")
        self.type_offre = self.create_instance(TypeOffre, nom=TypeOffre.CRIF)
        self.statut = self.create_instance(Statut, nom=Statut.NON_DEFINI)

        self.formation = self.create_instance(
            Formation,
            nom="Formation Prospection",
            centre=self.centre,
            type_offre=self.type_offre,
            statut=self.statut,
            start_date=self.date_debut,
            end_date=self.date_debut + timedelta(days=30),
        )

        self.partenaire = self.create_instance(Partenaire, nom="Partenaire Test")
        self.prospection = Prospection.objects.create(
            formation=self.formation,
            partenaire=self.partenaire,
            type_contact=ProspectionChoices.TYPE_PREMIER_CONTACT,
            motif=ProspectionChoices.MOTIF_PARTENARIAT,
            statut=ProspectionChoices.STATUT_A_FAIRE,
            objectif=ProspectionChoices.OBJECTIF_PARTENARIAT,
            created_by=self.user,
        )

    def create_valid_rapport(self, **kwargs):
        base_kwargs = {
            "nom": "Rapport Test",
            "type_rapport": Rapport.TYPE_OCCUPATION,
            "periode": Rapport.PERIODE_QUOTIDIEN,
            "date_debut": self.date_debut,
            "date_fin": self.date_fin,
            "format": Rapport.FORMAT_PDF,
            "centre": self.centre,
            "formation": self.formation,
            "type_offre": self.type_offre,
            "statut": self.statut,
            "donnees": {"inscrits": 42},
            "created_by": self.user,
        }
        base_kwargs.update(kwargs)
        return Rapport.objects.create(**base_kwargs)

    def test_str_repr(self):
        rapport = self.create_valid_rapport()
        self.assertIn("Rapport Test", str(rapport))
        self.assertIn("occupation", repr(rapport))

    def test_clean_date_incoherente(self):
        rapport = self.create_valid_rapport()
        rapport.date_debut = self.date_fin + timedelta(days=1)
        with self.assertRaises(ValidationError) as ctx:
            rapport.full_clean()
        self.assertIn("date_debut", ctx.exception.message_dict)

    def test_clean_periode_excessive(self):
        rapport = self.create_valid_rapport(periode=Rapport.PERIODE_HEBDOMADAIRE)
        rapport.date_fin = rapport.date_debut + timedelta(days=10)
        with self.assertRaises(ValidationError) as ctx:
            rapport.full_clean()
        self.assertIn("date_fin", ctx.exception.message_dict)

    def test_clean_periode_personnalisee_pas_limitee(self):
        rapport = self.create_valid_rapport(periode=Rapport.PERIODE_PERSONNALISE)
        rapport.date_fin = rapport.date_debut + timedelta(days=300)
        try:
            rapport.full_clean()
        except ValidationError:
            self.fail("ValidationError levée alors que la période est personnalisée")

    def test_to_serializable_dict_complet(self):
        rapport = self.create_valid_rapport()
        data = rapport.to_serializable_dict()
        self.assertEqual(data["type_rapport_display"], rapport.get_type_rapport_display())
        self.assertEqual(data["periode_display"], rapport.get_periode_display())
        self.assertEqual(data["format_display"], rapport.get_format_display())

    def test_invalidate_caches_efface_cles(self):
        rapport = self.create_valid_rapport()
        cache.set(f"rapport_{rapport.pk}", "valeur")
        cache.set(f"rapport_liste_{rapport.type_rapport}", "valeur")
        cache.set(f"rapport_recent_{rapport.type_rapport}", "valeur")

        rapport.invalidate_caches()

        self.assertIsNone(cache.get(f"rapport_{rapport.pk}"))
        self.assertIsNone(cache.get(f"rapport_liste_{rapport.type_rapport}"))
        self.assertIsNone(cache.get(f"rapport_recent_{rapport.type_rapport}"))
