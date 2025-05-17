from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model

from ...models.formations import Formation, Centre, HistoriqueFormation, TypeOffre, Statut
from ...models.evenements import Evenement
from ...api.serializers.evenements_serializers import EvenementSerializer

User = get_user_model()


class EvenementSerializerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='pass')
        self.formation = Formation.objects.create(nom="Formation Hist", centre=Centre.objects.create(nom="X"), type_offre=TypeOffre.objects.create(nom="crif"), statut=Statut.objects.create(nom="formation_en_cours", couleur="#123456"), created_by=self.user)
        self.histo = HistoriqueFormation.objects.create(
            formation=self.formation,
            champ_modifie="nom",
            ancienne_valeur="Old",
            nouvelle_valeur="New",
            commentaire="Nom modifié",
            created_by=self.user
        )

    def test_serializer_valid_data(self):
        data = {
            "formation_id": self.formation.id,
            "type_evenement": Evenement.TypeEvenement.JOB_DATING,
            "event_date": (date.today() + timedelta(days=5)).isoformat(),
            "lieu": "Salle A",
            "participants_prevus": 20,
            "participants_reels": 15,
        }
        serializer = EvenementSerializer(data=data, context={"request": None})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_serializer_autre_requires_description(self):
        data = {
            "formation_id": self.formation.id,
            "type_evenement": Evenement.TypeEvenement.AUTRE,
            "event_date": date.today().isoformat(),
        }
        serializer = EvenementSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("description_autre", serializer.errors)

    def test_output_representation(self):
        evenement = Evenement.objects.create(
            formation=self.formation,
            type_evenement=Evenement.TypeEvenement.FORUM,
            event_date=date.today(),
            participants_prevus=10,
            participants_reels=7,
            created_by=self.user
        )
        serializer = EvenementSerializer(instance=evenement)
        rep = serializer.data
        self.assertIn("success", rep)
        self.assertIn("data", rep)
        self.assertEqual(rep["data"]["type_evenement"], Evenement.TypeEvenement.FORUM)
        self.assertEqual(rep["data"]["taux_participation"], 70.0)

    def test_invalid_participation(self):
        data = {
            "formation_id": self.formation.id,
            "type_evenement": Evenement.TypeEvenement.JPO,
            "event_date": date.today().isoformat(),
            "participants_prevus": 10,
            "participants_reels": 20,
        }
        serializer = EvenementSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
