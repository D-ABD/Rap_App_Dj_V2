"""
Tests unitaires pour tous les modèles de l'application Rap_App.
Corrigé automatiquement.
"""

from django.test import TestCase
from django.utils import timezone
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from rap_app.models import (
    Centre, Statut, TypeOffre, Formation, Commentaire,
    Evenement, Document, Partenaire, Company, Prospection,
    Rapport, HistoriqueFormation
)

User = get_user_model()


class BaseModelTestMixin:
    def assertTimestampsExist(self, instance):
        self.assertIsNotNone(instance.created_at)
        self.assertIsNotNone(instance.updated_at)


class TestCentreModel(TestCase, BaseModelTestMixin):
    def test_creation_centre(self):
        centre = Centre.objects.create(nom="Test Centre", code_postal="75000")
        self.assertEqual(str(centre), "Test Centre")
        self.assertEqual(centre.full_address(), "Test Centre (75000)")
        self.assertTimestampsExist(centre)


class TestStatutModel(TestCase):
    def test_statut_badge_html(self):
        statut = Statut.objects.create(nom="formation_en_cours", couleur="#ff0000")
        badge = statut.get_badge_html()
        self.assertIn("Formation en cours", badge)
        self.assertIn("#ff0000", badge.lower())


class TestTypeOffreModel(TestCase):
    def test_type_offre_badge_html(self):
        type_offre = TypeOffre.objects.create(nom="poec", couleur="#0000ff")
        badge = type_offre.get_badge_html()
        self.assertIn("poec", badge.lower())
        self.assertIn("#0000ff", badge.lower())


class TestFormationModel(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser")
        self.centre = Centre.objects.create(nom="Centre A", code_postal="75000")
        self.type_offre = TypeOffre.objects.create(nom="poec", couleur="#00ff00")
        self.statut = Statut.objects.create(nom="formation_en_cours", couleur="#123456")
        self.formation = Formation.objects.create(
            nom="Formation Test",
            centre=self.centre,
            type_offre=self.type_offre,
            statut=self.statut,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=10),
            prevus_crif=10,
            prevus_mp=5,
            inscrits_crif=6,
            inscrits_mp=3,
            nombre_candidats=15,
            utilisateur=self.user
        )

    def test_indicateurs(self):
        self.assertEqual(self.formation.get_total_places(), 15)
        self.assertEqual(self.formation.get_total_inscrits(), 9)
        self.assertAlmostEqual(self.formation.get_taux_transformation(), 60.0)
        self.assertAlmostEqual(self.formation.get_taux_saturation(), 60.0)

    def test_commentaire_evenement(self):
        commentaire = self.formation.add_commentaire(self.user, "Test com")
        self.assertEqual(commentaire.contenu, "Test com")
        self.assertEqual(self.formation.dernier_commentaire, "Test com")

        from rap_app.models.evenements import Evenement
        event = self.formation.add_evenement(type_evenement=Evenement.INFO_PRESENTIEL, event_date=date.today())
        self.assertEqual(event.formation, self.formation)


class TestCommentaireModel(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user")
        self.centre = Centre.objects.create(nom="Centre B", code_postal="69000")
        self.type_offre = TypeOffre.objects.create(nom="crif", couleur="#999999")
        self.statut = Statut.objects.create(nom="formation_en_cours", couleur="#222222")
        self.formation = Formation.objects.create(
            nom="Formation X",
            centre=self.centre,
            type_offre=self.type_offre,
            statut=self.statut
        )

    def test_commentaire_clean_html(self):
        commentaire = Commentaire.objects.create(
            formation=self.formation,
            utilisateur=self.user,
            contenu="<script>alert('x')</script><b>Bold</b>"
        )
        self.assertEqual(commentaire.contenu, "alert('x')Bold")


class TestEvenementModel(TestCase):
    def setUp(self):
        self.centre = Centre.objects.create(nom="Centre Event", code_postal="13000")
        self.type_offre = TypeOffre.objects.create(nom="poec", couleur="#00ff00")
        self.statut = Statut.objects.create(nom="formation_a_annuler", couleur="#abcdef")
        self.formation = Formation.objects.create(
            nom="Formation Y",
            centre=self.centre,
            type_offre=self.type_offre,
            statut=self.statut
        )

    def test_evenement_creation(self):
        from rap_app.models.evenements import Evenement
        event = Evenement.objects.create(
            formation=self.formation,
            type_evenement=Evenement.INFO_PRESENTIEL,
            event_date=date.today()
        )
        self.assertEqual(event.formation, self.formation)


class TestPartenaireModel(TestCase):
    def test_slug_generation(self):
        partenaire = Partenaire.objects.create(nom="Partenaire & Co", secteur_activite="Informatique")
        self.assertIn("partenaire-co", partenaire.slug)
        self.assertEqual(str(partenaire), "Partenaire & Co")


class TestCompanyModel(TestCase):
    def test_creation_company(self):
        company = Company.objects.create(name="Entreprise X")
        self.assertEqual(company.name, "Entreprise X")


class TestProspectionModel(TestCase):
    def test_creation_prospection(self):
        centre = Centre.objects.create(nom="Centre Prospection", code_postal="99999")
        type_offre = TypeOffre.objects.create(nom="poec", couleur="#888888")
        statut = Statut.objects.create(nom="formation_en_cours", couleur="#000000")
        company = Company.objects.create(name="Company Y")
        formation = Formation.objects.create(nom="Formation P", centre=centre, type_offre=type_offre, statut=statut)
        prospection = Prospection.objects.create(company=company, formation=formation, statut="nouveau")
        self.assertEqual(prospection.formation, formation)
        self.assertEqual(prospection.company, company)


class TestRapportModel(TestCase):
    def test_creation_rapport(self):
        centre = Centre.objects.create(nom="Centre Rapport", code_postal="12345")
        type_offre = TypeOffre.objects.create(nom="crif", couleur="#222222")
        statut = Statut.objects.create(nom="formation_en_cours", couleur="#444444")
        formation = Formation.objects.create(nom="Formation R", centre=centre, type_offre=type_offre, statut=statut)
        rapport = Rapport.objects.create(
            formation=formation,
            date_debut=date.today(),
            date_fin=date.today() + timedelta(days=1)
        )
        self.assertEqual(rapport.formation, formation)

from django.test import TestCase
from django.utils import timezone
from datetime import date

from rap_app.models.centres import Centre
from rap_app.models.prepacomp import Semaine, PrepaCompGlobal, NOMS_MOIS


class PrepaModelsTestCase(TestCase):

    def setUp(self):
        self.centre = Centre.objects.create(nom="Centre Test", objectif_annuel_prepa=120, objectif_hebdomadaire_prepa=10)
        self.semaine = Semaine.objects.create(
            centre=self.centre,
            annee=2024,
            mois=1,
            numero_semaine=1,
            date_debut_semaine=date(2024, 1, 1),
            date_fin_semaine=date(2024, 1, 7),
            objectif_annuel_prepa=120,
            objectif_mensuel_prepa=40,
            objectif_hebdo_prepa=10,
            nombre_places_ouvertes=12,
            nombre_prescriptions=10,
            nombre_presents_ic=8,
            nombre_adhesions=4,
            departements={"75": 2},
            nombre_par_atelier={"AT1": 1, "AT2": 2}
        )

        self.bilan = PrepaCompGlobal.objects.create(
            centre=self.centre,
            annee=2024,
            total_candidats=20,
            total_prescriptions=18,
            adhesions=6,
            total_presents=8,
            total_places_ouvertes=12
        )

    def test_str_semaine(self):
        self.assertIn("Semaine 1", str(self.semaine))

    def test_taux_transformation(self):
        self.assertEqual(self.semaine.taux_transformation(), 50.0)
        self.assertEqual(self.semaine.taux_adhesion(), 50.0)

    def test_pourcentage_objectif(self):
        self.assertEqual(self.semaine.pourcentage_objectif(), 40.0)

    def test_total_par_departement(self):
        self.assertEqual(self.semaine.total_adhesions_departement("75"), 2)
        self.assertEqual(self.semaine.total_adhesions_departement("93"), 0)

    def test_total_par_atelier(self):
        self.assertEqual(self.semaine.total_par_atelier("AT1"), 1)
        self.assertEqual(self.semaine.total_par_atelier("AT2"), 2)
        self.assertEqual(self.semaine.total_par_atelier("AT4"), 0)

    def test_nom_mois(self):
        self.assertEqual(self.semaine.nom_mois(), "Janvier")

    def test_stats_globales_par_atelier(self):
        stats = Semaine.stats_globales_par_atelier(2024)
        self.assertTrue(any(s["code"] == "AT1" and s["total"] == 1 for s in stats))

    def test_prepa_comp_global_str(self):
        self.assertIn("Bilan 2024", str(self.bilan))

    def test_taux_transformation_bilan(self):
        self.assertEqual(self.bilan.taux_transformation(), 75.0)

    def test_taux_objectif_annee(self):
        self.assertEqual(self.bilan.taux_objectif_annee(), 5.0)

    def test_objectifs_par_centre(self):
        resultats = PrepaCompGlobal.objectifs_par_centre(2024)
        self.assertEqual(len(resultats), 1)
        self.assertEqual(resultats[0]["objectif_annuel_defini"], 120)
        self.assertGreaterEqual(resultats[0]["objectif_calculé"], 4)

    def test_stats_par_mois(self):
        stats = PrepaCompGlobal.stats_par_mois(2024, centre=self.centre)
        janvier = next((s for s in stats if s["mois_num"] == 1), None)
        self.assertIsNotNone(janvier)
        self.assertEqual(janvier["adhesions"], 4)
        self.assertEqual(janvier["objectif_hebdo"], 10)

    def test_creer_semaine_courante(self):
        semaine = Semaine.creer_semaine_courante(self.centre)
        self.assertEqual(semaine.centre, self.centre)
        self.assertTrue(semaine.numero_semaine > 0)

    def test_objectif_annuel_global(self):
        total = PrepaCompGlobal.objectif_annuel_global()
        self.assertEqual(total, 120)

    def test_objectif_hebdo_global(self):
        total = PrepaCompGlobal.objectif_hebdo_global(2024)
        self.assertEqual(total, 10)

from django.test import TestCase
from datetime import date
from rap_app.models.prepacomp import Semaine, PrepaCompGlobal, NOMS_ATELIERS
from rap_app.models.centres import Centre

class PrepaCompTests(TestCase):
    def setUp(self):
        self.centre = Centre.objects.create(nom="Test Centre", objectif_annuel_prepa=100, objectif_hebdomadaire_prepa=10)
        self.semaine = Semaine.objects.create(
            centre=self.centre,
            annee=2025,
            mois=1,
            numero_semaine=1,
            date_debut_semaine=date(2025, 1, 1),
            date_fin_semaine=date(2025, 1, 7),
            nombre_places_ouvertes=20,
            nombre_prescriptions=15,
            nombre_presents_ic=10,
            nombre_adhesions=5,
            nombre_par_atelier={"AT1": 2, "AT2": 3},
            departements={"75": 4, "92": 1}
        )
        self.bilan = PrepaCompGlobal.objects.create(
            centre=self.centre,
            annee=2025,
            total_candidats=100,
            total_prescriptions=60,
            adhesions=50,
            total_presents=80,
            total_places_ouvertes=90
        )

    def test_str_semaine(self):
        self.assertIn("Semaine", str(self.semaine))
        self.assertIn("Test Centre", str(self.semaine))

    def test_taux_transformation(self):
        self.assertEqual(self.semaine.taux_transformation(), 50.0)

    def test_taux_objectif(self):
        self.assertEqual(self.bilan.taux_objectif_annee(), 50.0)

    def test_total_par_atelier(self):
        self.assertEqual(self.semaine.total_par_atelier("AT1"), 2)
        self.assertEqual(self.semaine.total_par_atelier("AT5"), 0)

    def test_total_adhesions_departement(self):
        self.assertEqual(self.semaine.total_adhesions_departement("75"), 4)
        self.assertEqual(self.semaine.total_adhesions_departement("78"), 0)

    def test_nom_mois(self):
        self.assertEqual(self.semaine.nom_mois(), "Janvier")

    def test_ateliers_nommes(self):
        noms = self.semaine.ateliers_nommés
        self.assertTrue(any(d['code'] == "AT1" and d['valeur'] == 2 for d in noms))

    def test_objectif_global_annuel(self):
        self.assertEqual(PrepaCompGlobal.objectif_annuel_global(), 100)

    def test_objectif_global_hebdo(self):
        self.assertEqual(PrepaCompGlobal.objectif_hebdo_global(2025), 10)

    def test_stats_par_mois(self):
        stats = PrepaCompGlobal.stats_par_mois(2025, self.centre)
        self.assertTrue(len(stats), 12)
        mois_1 = stats[0]
        self.assertEqual(mois_1["adhesions"], 5)
        self.assertEqual(mois_1["taux_transformation"], 50.0)

    def test_stats_globales_par_atelier(self):
        result = Semaine.stats_globales_par_atelier(2025)
        at1 = next((r for r in result if r["code"] == "AT1"), None)
        self.assertIsNotNone(at1)
        self.assertEqual(at1["total"], 2)
