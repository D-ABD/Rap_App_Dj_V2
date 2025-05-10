
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

from ...models import Formation, Centre, TypeOffre, Statut, HistoriqueFormation, Partenaire, Evenement
from .setup_base_tests import BaseModelTestSetupMixin


class FormationModelTest(BaseModelTestSetupMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.centre = self.create_instance(Centre, nom="Centre Test")
        self.type_offre = self.create_instance(TypeOffre, nom=TypeOffre.CRIF)
        self.statut = self.create_instance(Statut, nom=Statut.NON_DEFINI)
        self.formation = self.create_instance(
            Formation,
            nom="Test Formation",
            centre=self.centre,
            type_offre=self.type_offre,
            statut=self.statut,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),
        )

    def test_model_creation(self):
        self.assertEqual(str(self.formation), "Test Formation (Centre Test)")
        self.assertEqual(self.formation.status_temporel, "active")

    def test_validation_dates(self):
        self.formation.start_date = timezone.now().date() + timedelta(days=10)
        self.formation.end_date = timezone.now().date()
        with self.assertRaises(ValidationError):
            self.formation.full_clean()

    def test_total_places_and_inscrits_properties(self):
        self.formation.prevus_crif = 10
        self.formation.prevus_mp = 5
        self.formation.inscrits_crif = 7
        self.formation.inscrits_mp = 3
        self.assertEqual(self.formation.total_places, 15)
        self.assertEqual(self.formation.total_inscrits, 10)
        self.assertEqual(self.formation.places_disponibles, 5)

    def test_taux_saturation_and_transformation(self):
        self.formation.prevus_crif = 5
        self.formation.prevus_mp = 5
        self.formation.inscrits_crif = 5
        self.formation.inscrits_mp = 3
        self.formation.nombre_candidats = 10
        self.assertEqual(self.formation.taux_saturation, 80.0)
        self.assertEqual(self.formation.taux_transformation, 80.0)

    def test_is_active_future_past(self):
        today = timezone.now().date()
        self.formation.start_date = today + timedelta(days=1)
        self.formation.end_date = today + timedelta(days=10)
        self.assertTrue(self.formation.is_future)
        self.formation.start_date = today - timedelta(days=10)
        self.formation.end_date = today - timedelta(days=1)
        self.assertTrue(self.formation.is_past)

    def test_add_commentaire(self):
        commentaire = self.formation.add_commentaire(user=self.user, contenu="Test commentaire", saturation=75)
        self.assertEqual(commentaire.formation, self.formation)
        self.assertEqual(self.formation.dernier_commentaire, "Test commentaire")

    def test_add_document(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        file = SimpleUploadedFile("test.pdf", b"content")
        doc = self.formation.add_document(user=self.user, fichier=file, titre="Doc test")
        self.assertEqual(doc.formation, self.formation)

    def test_add_evenement(self):
        """✅ Vérifie l'ajout d'un événement de type 'Autre' avec description personnalisée."""
        from rap_app.models.evenements import Evenement

        date = timezone.now().date()
        evenements_avant = self.formation.evenements.count()

        evenement = self.formation.add_evenement(
            type_evenement=Evenement.TypeEvenement.AUTRE,
            description_autre="Présentation de fin d'année",
            event_date=date,
            user=self.user
        )

        self.formation.refresh_from_db()

        self.assertEqual(evenement.formation, self.formation)
        self.assertEqual(evenement.type_evenement, Evenement.TypeEvenement.AUTRE)
        self.assertEqual(evenement.description_autre, "Présentation de fin d'année")
        self.assertEqual(evenement.event_date, date)
        self.assertEqual(self.formation.evenements.count(), evenements_avant + 1)

    def test_update_saturation_from_commentaires(self):
        self.formation.add_commentaire(user=self.user, contenu="Com1", saturation=70)
        self.formation.add_commentaire(user=self.user, contenu="Com2", saturation=90)
        updated = self.formation.update_saturation_from_commentaires()
        self.assertTrue(updated)
        self.assertEqual(self.formation.saturation, 80.0)

    def test_to_serializable_dict(self):
        data = self.formation.to_serializable_dict()
        self.assertIn("nom", data)
        self.assertIn("statut", data)
        self.assertIn("total_places", data)

    def test_duplicate_formation(self):
        new_form = self.formation.duplicate(user=self.user)
        self.assertNotEqual(new_form.pk, self.formation.pk)
        self.assertTrue("Copie" in new_form.nom)

    def test_manager_methods(self):
        actives = Formation.objects.formations_actives()
        self.assertIn(self.formation, actives)

    def test_manager_recherche(self):
        results = Formation.objects.recherche(texte="Test")
        self.assertIn(self.formation, results)

    def test_increment_attendees(self):
        updated = Formation.objects.increment_attendees(self.formation.pk, count=2, crif=True, user=self.user)
        self.assertEqual(updated.inscrits_crif, 2)

    def test_get_csv_fields_and_row(self):
        row = self.formation.to_csv_row()
        self.assertEqual(row[1], self.formation.nom)

    def test_get_stats_par_mois(self):
        stats = Formation.get_stats_par_mois()
        self.assertTrue(isinstance(stats, dict))

    def test_clean_warns_on_excessive_inscrits(self):
        self.formation.prevus_crif = 5
        self.formation.inscrits_crif = 10
        self.formation.prevus_mp = 3
        self.formation.inscrits_mp = 6
        self.formation.full_clean()  # ne lève pas d'erreur, mais log un warning

    def test_historique_created_on_change(self):
        old_name = self.formation.nom
        self.formation.nom = "Nouveau nom"
        self.formation.save(user=self.user)
        historique = HistoriqueFormation.objects.filter(formation=self.formation, champ_modifie="nom").first()
        self.assertIsNotNone(historique)
        self.assertEqual(historique.ancienne_valeur, old_name)
        self.assertEqual(historique.nouvelle_valeur, "Nouveau nom")

    def test_status_color_returns_expected_value(self):
        self.assertTrue(self.formation.get_status_color().startswith("#"))

    def test_add_partenaire(self):
        """✅ Vérifie l'ajout d'un partenaire à une formation avec historique."""
        partenaire = self.create_instance(Partenaire, nom="Entreprise X")
        partenaires_avant = self.formation.partenaires.count()

        self.formation.add_partenaire(partenaire=partenaire, user=self.user)

        self.formation.refresh_from_db()
        self.assertEqual(self.formation.partenaires.count(), partenaires_avant + 1)
        self.assertIn(partenaire, self.formation.partenaires.all())

        historique = HistoriqueFormation.objects.filter(
            formation=self.formation, champ_modifie="partenaire", nouvelle_valeur=partenaire.nom
        ).first()
        self.assertIsNotNone(historique)
        self.assertEqual(historique.created_by, self.user)

    def test_get_partenaires(self):
        """✅ Vérifie que les partenaires sont correctement retournés via get_partenaires()."""
        partenaire1 = self.create_instance(Partenaire, nom="Entreprise Y")
        partenaire2 = self.create_instance(Partenaire, nom="Entreprise Z")

        self.formation.partenaires.add(partenaire1, partenaire2)

        partenaires = self.formation.get_partenaires()
        self.assertIn(partenaire1, partenaires)
        self.assertIn(partenaire2, partenaires)

