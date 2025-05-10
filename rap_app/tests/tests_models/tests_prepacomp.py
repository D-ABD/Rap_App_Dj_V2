from django.test import TestCase
from django.utils import timezone
from datetime import timedelta, date

from ...models.centres import Centre
from ...models.prepacomp import Semaine, PrepaCompGlobal
from .setup_base_tests import BaseModelTestSetupMixin


class SemaineModelTest(BaseModelTestSetupMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.centre = self.create_instance(Centre, nom="Centre Test")
        self.date_debut = date.today() - timedelta(days=date.today().weekday())  # Lundi
        self.date_fin = self.date_debut + timedelta(days=6)  # Dimanche

        self.semaine = Semaine.objects.create(
            centre=self.centre,
            date_debut_semaine=self.date_debut,
            date_fin_semaine=self.date_fin,
            numero_semaine=self.date_debut.isocalendar()[1],
            annee=self.date_debut.year,
            mois=self.date_debut.month,
            objectif_hebdo_prepa=10,
            nombre_adhesions=8,
            nombre_prescriptions=10,
            nombre_presents_ic=10,
            departements={"75": 8},
            nombre_par_atelier={"AT1": 5, "AT2": 3},
            created_by=self.user
        )

    def test_str_and_repr(self):
        self.assertIn("Semaine", str(self.semaine))
        self.assertIn("num=", repr(self.semaine))

    def test_is_courante(self):
        self.assertTrue(self.semaine.is_courante)

    def test_taux_adhesion_transformation_objectif(self):
        self.assertEqual(self.semaine.taux_adhesion(), 80.0)
        self.assertEqual(self.semaine.taux_transformation(), 80.0)
        self.assertEqual(self.semaine.pourcentage_objectif(), 80.0)

    def test_ecart_objectif(self):
        self.assertEqual(self.semaine.ecart_objectif, -2)

    def test_departements_nommes(self):
        nommes = self.semaine.departements_nommés
        self.assertEqual(nommes[0]["code"], "75")

    def test_ateliers_nommes(self):
        self.assertEqual(len(self.semaine.ateliers_nommés), 2)

    def test_total_adhesions_departement(self):
        self.assertEqual(self.semaine.total_adhesions_departement("75"), 8)

    def test_total_par_atelier(self):
        self.assertEqual(self.semaine.total_par_atelier("AT1"), 5)

    def test_to_serializable_dict(self):
        data = self.semaine.to_serializable_dict()
        self.assertEqual(data["adhesions"], 8)
        self.assertEqual(data["centre"]["nom"], self.centre.nom)

    def test_clean_invalid_json(self):
        self.semaine.departements = "not a dict"
        with self.assertRaises(Exception):
            self.semaine.full_clean()

    def test_semaine_suivante_et_precedente(self):
        semaine_suiv = Semaine.create_for_week(self.centre, self.date_fin + timedelta(days=1), created_by=self.user)
        self.assertEqual(self.semaine.semaine_suivante, semaine_suiv)
        self.assertEqual(semaine_suiv.semaine_precedente, self.semaine)

    def test_save_triggers_prepa_global_update(self):
        self.semaine.nombre_adhesions = 9
        self.semaine.departements = {"75": 9}  # ✅ cohérent avec nombre_adhesions
        self.semaine.save(user=self.user)
        pg = PrepaCompGlobal.objects.get(centre=self.centre, annee=self.semaine.annee)
        self.assertEqual(pg.adhesions, 9)



class PrepaCompGlobalModelTest(BaseModelTestSetupMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.centre = self.create_instance(Centre, nom="Centre Test")
        self.global_stat = PrepaCompGlobal.objects.create(
            centre=self.centre,
            annee=date.today().year,
            adhesions=40,
            total_presents=50,
            total_prescriptions=60,
            objectif_annuel_prepa=100,
            objectif_hebdomadaire_prepa=2,
            created_by=self.user
        )

    def test_taux_transformation_et_objectif(self):
        self.assertEqual(self.global_stat.taux_transformation(), 80.0)
        self.assertEqual(self.global_stat.taux_objectif_annee(), 40.0)

    def test_objectif_restant_et_semaines_restantes(self):
        self.assertTrue(self.global_stat.objectif_restant > 0)
        self.assertTrue(self.global_stat.semaines_restantes <= 52)

    def test_adhesions_hebdo_necessaires(self):
        self.assertGreaterEqual(self.global_stat.adhesions_hebdo_necessaires, 0)

    def test_moyenne_hebdomadaire(self):
        Semaine.create_for_week(self.centre, date.today(), nombre_adhesions=40, created_by=self.user)
        self.global_stat.recalculate_from_semaines()
        self.assertGreaterEqual(self.global_stat.moyenne_hebdomadaire, 0)

    def test_to_serializable_dict(self):
        data = self.global_stat.to_serializable_dict()
        self.assertIn("adhesions", data)
        self.assertIn("centre", data)
