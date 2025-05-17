from rest_framework.test import APITestCase
from rap_app.models.statut import Statut
from rap_app.api.serializers.statut_serializers import StatutSerializer


class StatutSerializerTestCase(APITestCase):
    def setUp(self):
        self.default_data = {
            "nom": Statut.RECRUTEMENT_EN_COURS,
            "couleur": "#4CAF50",
        }

    def test_valid_serializer(self):
        serializer = StatutSerializer(data=self.default_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["nom"], Statut.RECRUTEMENT_EN_COURS)

    def test_missing_description_autre_for_autre(self):
        data = {
            "nom": Statut.AUTRE,
            "couleur": "#795548",
            "description_autre": ""
        }
        serializer = StatutSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("description_autre", serializer.errors)

    def test_invalid_hex_color(self):
        data = {
            "nom": Statut.RECRUTEMENT_EN_COURS,
            "couleur": "vert"
        }
        serializer = StatutSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("couleur", serializer.errors)

    def test_to_representation(self):
        statut = Statut.objects.create(
            nom=Statut.QUASI_PLEINE,
            couleur="#3F51B5",
        )
        serializer = StatutSerializer(statut)
        data = serializer.data
        self.assertEqual(data["id"], statut.id)
        self.assertEqual(data["libelle"], statut.get_nom_display())
        self.assertIn("badge_html", data)
        self.assertIn("#3F51B5", data["badge_html"])

    def test_serializer_with_valid_autre(self):
        data = {
            "nom": Statut.AUTRE,
            "couleur": "#795548",
            "description_autre": "Statut personnalisé"
        }
        serializer = StatutSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["description_autre"], "Statut personnalisé")
