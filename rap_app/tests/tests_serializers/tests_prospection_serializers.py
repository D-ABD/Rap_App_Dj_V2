from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from ...models.centres import Centre
from ...models.custom_user import CustomUser
from ...models.formations import Formation
from ...models.partenaires import Partenaire
from ...models.statut import Statut
from ...models.types_offre import TypeOffre

from ...api.serializers.prospection_serializers import ChangerStatutSerializer, ProspectionSerializer


class ProspectionSerializerTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass"
        )

        centre = Centre.objects.create(nom="Centre Test", code_postal="75000")
        statut = Statut.objects.create(nom="non_defini", couleur="#000000")
        type_offre = TypeOffre.objects.create(nom="poec", couleur="#FF0000")

        self.formation = Formation.objects.create(
            nom="Formation Z",
            centre=centre,
            statut=statut,
            type_offre=type_offre,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=5),
            created_by=self.user
        )

        self.partenaire = Partenaire.objects.create(nom="Entreprise Y", type="entreprise")

        self.valid_data = {
            "partenaire": self.partenaire.id,
            "formation": self.formation.id,
            "date_prospection": timezone.now().isoformat(),
            "type_contact": ProspectionChoices.TYPE_PREMIER_CONTACT,
            "motif": ProspectionChoices.MOTIF_PARTENARIAT,
            "statut": ProspectionChoices.STATUT_EN_COURS,
            "objectif": ProspectionChoices.OBJECTIF_PRESENTATION,
            "commentaire": "Test"
        }

    def test_serializer_valid(self):
        serializer = ProspectionSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_accepted_requires_contract_objective(self):
        data = self.valid_data.copy()
        data.update({
            "statut": ProspectionChoices.STATUT_ACCEPTEE,
            "objectif": ProspectionChoices.OBJECTIF_PRESENTATION
        })
        serializer = ProspectionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_refused_or_cancelled_requires_comment(self):
        for statut in [ProspectionChoices.STATUT_REFUSEE, ProspectionChoices.STATUT_ANNULEE]:
            data = self.valid_data.copy()
            data.update({"statut": statut, "commentaire": ""})
            serializer = ProspectionSerializer(data=data)
            self.assertFalse(serializer.is_valid())
            self.assertIn("commentaire", serializer.errors)

    def test_output_fields(self):
        prospection = Prospection.objects.create(
            partenaire=self.partenaire,
            formation=self.formation,
            type_contact=ProspectionChoices.TYPE_PREMIER_CONTACT,
            motif=ProspectionChoices.MOTIF_PARTENARIAT,
            statut=ProspectionChoices.STATUT_EN_COURS,
            objectif=ProspectionChoices.OBJECTIF_PRESENTATION,
            commentaire="Test",
            created_by=self.user
        )
        serializer = ProspectionSerializer(instance=prospection)
        data = serializer.data

        self.assertIn("is_active", data)
        self.assertIn("relance_necessaire", data)
        self.assertIn("prochain_contact", data)
        self.assertTrue(isinstance(data["is_active"], bool))

    def test_create_instance(self):
        serializer = ProspectionSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        instance = serializer.save(created_by=self.user)
        self.assertIsInstance(instance, Prospection)

    def test_invalid_partial_update(self):
        prospection = Prospection.objects.create(
            partenaire=self.partenaire,
            formation=self.formation,
            type_contact=ProspectionChoices.TYPE_PREMIER_CONTACT,
            motif=ProspectionChoices.MOTIF_PARTENARIAT,
            statut=ProspectionChoices.STATUT_EN_COURS,
            objectif=ProspectionChoices.OBJECTIF_PRESENTATION,
            commentaire="Initial",
            created_by=self.user
        )
        serializer = ProspectionSerializer(
            instance=prospection,
            data={"statut": "invalid_status"},
            partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("statut", serializer.errors)


from ...models.prospection import HistoriqueProspection, Prospection, ProspectionChoices
from ...api.serializers.prospection_serializers import HistoriqueProspectionSerializer


class HistoriqueProspectionSerializerTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass",
            is_staff=True
        )

        self.centre = Centre.objects.create(nom="Centre X", code_postal="75000")
        self.statut = Statut.objects.create(nom="non_defini", couleur="#000000")
        self.type_offre = TypeOffre.objects.create(nom="poec", couleur="#FF0000")

        self.formation = Formation.objects.create(
            nom="Formation Test",
            centre=self.centre,
            statut=self.statut,
            type_offre=self.type_offre,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=10),
            created_by=self.user
        )

        self.partenaire = Partenaire.objects.create(nom="Entreprise A", type="entreprise")

        self.prospection = Prospection.objects.create(
            partenaire=self.partenaire,
            formation=self.formation,
            type_contact=ProspectionChoices.TYPE_PREMIER_CONTACT,
            motif=ProspectionChoices.MOTIF_PARTENARIAT,
            statut=ProspectionChoices.STATUT_EN_COURS,
            objectif=ProspectionChoices.OBJECTIF_PRESENTATION,
            commentaire="Initial",
            created_by=self.user
        )

        self.historique = HistoriqueProspection.objects.create(
            prospection=self.prospection,
            ancien_statut=ProspectionChoices.STATUT_A_FAIRE,
            nouveau_statut=ProspectionChoices.STATUT_EN_COURS,
            type_contact=ProspectionChoices.TYPE_PREMIER_CONTACT,
            commentaire="Premier contact établi",
            resultat="Rendez-vous pris",
            prochain_contact=timezone.now().date() + timedelta(days=7),
            moyen_contact=ProspectionChoices.MOYEN_TELEPHONE,
            created_by=self.user
        )
    
    def test_historique_serializer_output(self):
        serializer = HistoriqueProspectionSerializer(instance=self.historique)
        data = serializer.data

        # Structure de base (directe, sans success/message)
        self.assertEqual(data["ancien_statut"], "a_faire")
        self.assertEqual(data["ancien_statut_display"], "À faire")
        self.assertEqual(data["nouveau_statut"], "en_cours")
        self.assertEqual(data["nouveau_statut_display"], "En cours")
        self.assertIn("statut_avec_icone", data)

        statut_icon = data["statut_avec_icone"]
        self.assertEqual(statut_icon["statut"], "En cours")
        self.assertIn("fas fa-", statut_icon["icone"])
        self.assertIn("text-", statut_icon["classe"])


    def test_validate_prochain_contact_past_date(self):
        """Teste que la date de relance doit être dans le futur"""
        invalid_data = {
            "prochain_contact": timezone.now().date() - timedelta(days=1)
        }
        serializer = HistoriqueProspectionSerializer(
            instance=self.historique,
            data=invalid_data,
            partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("prochain_contact", serializer.errors)

    def test_serializer_with_future_contact_date(self):
        """Teste avec une date valide dans le futur"""
        valid_data = {
            "prochain_contact": timezone.now().date() + timedelta(days=10)
        }
        serializer = HistoriqueProspectionSerializer(
            instance=self.historique,
            data=valid_data,
            partial=True
        )
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(
            updated.prochain_contact,
            timezone.now().date() + timedelta(days=10)
        )

    def test_relance_urgente_calculation(self):
        """Teste le calcul de relance urgente"""
        # Cas non urgent (> 2 jours)
        self.historique.prochain_contact = timezone.now().date() + timedelta(days=3)
        self.assertFalse(self.historique.relance_urgente)
        
        # Cas urgent (<= 2 jours)
        self.historique.prochain_contact = timezone.now().date() + timedelta(days=1)
        self.assertTrue(self.historique.relance_urgente)

    def test_est_recent_calculation(self):
        """Teste le calcul est_recent"""
        # Cas récent (< 7 jours)
        self.historique.date_modification = timezone.now() - timedelta(days=3)
        self.assertTrue(self.historique.est_recent)
        
        # Cas non récent (>= 7 jours)
        self.historique.date_modification = timezone.now() - timedelta(days=8)
        self.assertFalse(self.historique.est_recent)

class ChangerStatutSerializerTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass"
        )
        
    def test_valid_status_change(self):
        data = {
            "statut": ProspectionChoices.STATUT_ACCEPTEE,
            "commentaire": "Contrat signé",
            "moyen_contact": ProspectionChoices.MOYEN_EMAIL
        }
        serializer = ChangerStatutSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_relance_status_sets_default_date(self):
        data = {
            "statut": ProspectionChoices.STATUT_A_RELANCER
        }
        serializer = ChangerStatutSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data["prochain_contact"],
            timezone.now().date() + timedelta(days=7)
        )

    def test_invalid_status(self):
        data = {
            "statut": "invalid_status"
        }
        serializer = ChangerStatutSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("statut", serializer.errors)