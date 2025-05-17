from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from ...models.custom_user import CustomUser
from ...models.centres import Centre
from ...models.statut import Statut
from ...models.types_offre import TypeOffre
from ...models.formations import Formation
from ...models.commentaires import Commentaire
from ...api.serializers.commentaires_serializers import CommentaireSerializer


class CommentaireSerializerTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass",
            is_staff=True
        )

        self.centre = Centre.objects.create(nom="Test Centre", code_postal="75000")
        self.statut = Statut.objects.create(nom="non_defini", couleur="#000000")
        self.type_offre = TypeOffre.objects.create(nom="poec", couleur="#FF0000")

        self.formation = Formation.objects.create(
            nom="Test Formation",
            centre=self.centre,
            statut=self.statut,
            type_offre=self.type_offre,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=10),
            created_by=self.user
        )

        self.commentaire = Commentaire.objects.create(
            formation=self.formation,
            contenu="Très bon formateur",
            saturation=80,
            created_by=self.user
        )

        self.valid_data = {
            "formation": self.formation.id,
            "contenu": "Contenu testé avec succès",
            "saturation": 60
        }

    def test_serializer_valide(self):
        serializer = CommentaireSerializer(data=self.valid_data, context={"request": self._mock_request()})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_serializer_contenu_vide(self):
        data = self.valid_data.copy()
        data["contenu"] = "   "
        serializer = CommentaireSerializer(data=data, context={"request": self._mock_request()})
        self.assertFalse(serializer.is_valid())
        self.assertIn("contenu", serializer.errors)

    def test_serializer_saturation_out_of_bounds(self):
        data = self.valid_data.copy()
        data["saturation"] = 150
        serializer = CommentaireSerializer(data=data, context={"request": self._mock_request()})
        self.assertFalse(serializer.is_valid())
        self.assertIn("saturation", serializer.errors)

    def test_create_commentaire(self):
        serializer = CommentaireSerializer(data=self.valid_data, context={"request": self._mock_request()})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        commentaire = serializer.save()
        self.assertEqual(commentaire.formation, self.formation)
        self.assertEqual(commentaire.created_by, self.user)
        self.assertEqual(commentaire.saturation, 60)

    def test_to_representation_structure(self):
        class MockView:
            action = "retrieve"

        serializer = CommentaireSerializer(
            instance=self.commentaire,
            context={"view": MockView()}
        )
        data = serializer.data
        self.assertIn("success", data)
        self.assertTrue(data["success"])
        self.assertIn("message", data)
        self.assertIn("data", data)
        self.assertEqual(data["data"]["formation_nom"], self.formation.nom)

    def _mock_request(self):
        class MockRequest:
            user = self.user
        return MockRequest()
