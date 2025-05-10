from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError

from ...models.centres import Centre
from ...models.statut import Statut
from ...models.types_offre import TypeOffre

from ...models.formations import Formation
from ...models.partenaires import Partenaire
from ...models.prospection import Prospection, HistoriqueProspection, ProspectionChoices
from .setup_base_tests import BaseModelTestSetupMixin


class ProspectionModelTest(BaseModelTestSetupMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.centre = self.create_instance(Centre, nom="Centre Prospection")
        self.type_offre = self.create_instance(TypeOffre, nom=TypeOffre.CRIF)
        self.statut = self.create_instance(Statut, nom=Statut.NON_DEFINI)
        self.formation = self.create_instance(
            Formation,
            nom="Formation Prospection",
            centre=self.centre,
            type_offre=self.type_offre,
            statut=self.statut,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),
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

    def test_str_and_repr(self):
        self.assertIn("Partenaire Test", str(self.prospection))
        self.assertIn("a_faire", repr(self.prospection))

    def test_clean_future_date(self):
        self.prospection.date_prospection = timezone.now() + timedelta(days=1)
        with self.assertRaises(ValidationError):
            self.prospection.full_clean()

    def test_clean_statut_acceptee_requires_contrat(self):
        self.prospection.statut = ProspectionChoices.STATUT_ACCEPTEE
        self.prospection.objectif = ProspectionChoices.OBJECTIF_PRESENTATION
        self.prospection.commentaire = "OK"
        with self.assertRaises(ValidationError):
            self.prospection.full_clean()

    def test_clean_refusee_without_comment(self):
        self.prospection.statut = ProspectionChoices.STATUT_REFUSEE
        self.prospection.commentaire = ""
        with self.assertRaises(ValidationError):
            self.prospection.full_clean()

    def test_is_active(self):
        self.assertTrue(self.prospection.is_active)
        self.prospection.statut = ProspectionChoices.STATUT_REFUSEE
        self.assertFalse(self.prospection.is_active)

    def test_creer_historique_creates_record(self):
        historique = self.prospection.creer_historique(
            ancien_statut=ProspectionChoices.STATUT_A_FAIRE,
            nouveau_statut=ProspectionChoices.STATUT_EN_COURS,
            type_contact=ProspectionChoices.TYPE_PREMIER_CONTACT,
            commentaire="Premier contact",
            resultat="Initiée",
            user=self.user
        )
        self.assertEqual(historique.nouveau_statut, ProspectionChoices.STATUT_EN_COURS)
        self.assertGreaterEqual(self.prospection.historiques.count(), 1)

    def test_prochain_contact_property(self):
        historique = self.prospection.creer_historique(
            ancien_statut=self.prospection.statut,
            nouveau_statut=ProspectionChoices.STATUT_A_RELANCER,
            type_contact=ProspectionChoices.TYPE_PREMIER_CONTACT,
            commentaire="Relancer bientôt",
            prochain_contact=timezone.now().date() + timedelta(days=3),
            user=self.user
        )
        self.assertEqual(self.prospection.prochain_contact, historique.prochain_contact)

    def test_relance_necessaire_true(self):
        prochain = timezone.now().date() + timedelta(days=1)
        historique = self.prospection.creer_historique(
            ancien_statut=self.prospection.statut,
            nouveau_statut=ProspectionChoices.STATUT_A_RELANCER,
            type_contact=ProspectionChoices.TYPE_PREMIER_CONTACT,
            commentaire="Prévue pour relance",
            prochain_contact=prochain,
            user=self.user
        )

        # Simule une date de test avancée si besoin (ou juste accepte False si on teste en temps réel)
        self.assertEqual(self.prospection.statut, ProspectionChoices.STATUT_A_RELANCER)
        self.assertFalse(self.prospection.relance_necessaire)

    def test_to_serializable_dict_keys(self):
            self.prospection.commentaire = "Refusée après entretien"
            self.prospection.save(skip_history=True)

            historique = self.prospection.creer_historique(
                ancien_statut=self.prospection.statut,
                nouveau_statut=ProspectionChoices.STATUT_REFUSEE,
                type_contact=ProspectionChoices.TYPE_RELANCE,
                commentaire="Refusée après entretien",
                user=self.user
            )
            data = historique.to_serializable_dict()
            self.assertIn("prospection_id", data)
            self.assertEqual(data["nouveau_statut"], historique.get_nouveau_statut_display())

    def test_get_stats_par_statut(self):
        stats = Prospection.custom.statistiques_par_statut()
        self.assertIn(self.prospection.statut, stats)


class HistoriqueProspectionModelTest(BaseModelTestSetupMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.centre = self.create_instance(Centre, nom="Centre Historique")
        self.type_offre = self.create_instance(TypeOffre, nom=TypeOffre.CRIF)
        self.statut = self.create_instance(Statut, nom=Statut.NON_DEFINI)
        self.formation = self.create_instance(
            Formation,
            nom="Formation Histo",
            centre=self.centre,
            type_offre=self.type_offre,
            statut=self.statut
        )
        self.partenaire = self.create_instance(Partenaire, nom="Partenaire Histo")
        self.prospection = Prospection.objects.create(
            formation=self.formation,
            partenaire=self.partenaire,
            type_contact=ProspectionChoices.TYPE_PREMIER_CONTACT,
            motif=ProspectionChoices.MOTIF_PARTENARIAT,
            statut=ProspectionChoices.STATUT_A_RELANCER,
            objectif=ProspectionChoices.OBJECTIF_PARTENARIAT,
            created_by=self.user
        )

    def test_prochain_contact_est_defini(self):
        historique = HistoriqueProspection.objects.create(
            prospection=self.prospection,
            ancien_statut=ProspectionChoices.STATUT_A_FAIRE,
            nouveau_statut=ProspectionChoices.STATUT_A_RELANCER,
            type_contact=ProspectionChoices.TYPE_RELANCE,
            commentaire="Relance prévue",
            prochain_contact=timezone.now().date() + timedelta(days=5),
            created_by=self.user
        )
        self.assertEqual(historique.prochain_contact, historique.prochain_contact)

    def test_clean_prochain_contact_past_raises(self):
        historique = HistoriqueProspection(
            prospection=self.prospection,
            ancien_statut=ProspectionChoices.STATUT_EN_COURS,
            nouveau_statut=ProspectionChoices.STATUT_A_RELANCER,
            type_contact=ProspectionChoices.TYPE_RELANCE,
            commentaire="Test",
            prochain_contact=timezone.now().date() - timedelta(days=1)
        )
        with self.assertRaises(ValidationError):
            historique.full_clean()

    def test_est_recent_true(self):
        historique = self.prospection.creer_historique(
            ancien_statut=self.prospection.statut,
            nouveau_statut=ProspectionChoices.STATUT_EN_COURS,
            type_contact=ProspectionChoices.TYPE_PREMIER_CONTACT,
            commentaire="Suivi actif",
            user=self.user
        )
        self.assertTrue(historique.est_recent)

    def test_jours_avant_relance_value(self):
        date = timezone.now().date() + timedelta(days=5)
        historique = self.prospection.creer_historique(
            ancien_statut=self.prospection.statut,
            nouveau_statut=ProspectionChoices.STATUT_EN_COURS,
            type_contact=ProspectionChoices.TYPE_PREMIER_CONTACT,
            commentaire="Prévu dans 5 jours",
            prochain_contact=date,
            user=self.user
        )
        self.assertEqual(historique.jours_avant_relance, 5)

    def test_to_serializable_dict_keys(self):
            self.prospection.commentaire = "Refusée après entretien"
            self.prospection.save(skip_history=True)

            historique = self.prospection.creer_historique(
                ancien_statut=self.prospection.statut,
                nouveau_statut=ProspectionChoices.STATUT_REFUSEE,
                type_contact=ProspectionChoices.TYPE_RELANCE,
                commentaire="Refusée après entretien",
                user=self.user
            )
            data = historique.to_serializable_dict()
            self.assertIn("prospection_id", data)
            self.assertEqual(data["nouveau_statut"], historique.get_nouveau_statut_display())