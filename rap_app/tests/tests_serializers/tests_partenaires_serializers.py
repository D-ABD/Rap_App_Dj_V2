# tests/test_partenaire_serializers.py

from django.test import TestCase
from ...models.partenaires import Partenaire
from ...api.serializers.partenaires_serializers import PartenaireSerializer

class PartenaireSerializerTestCase(TestCase):
    def setUp(self):
        self.valid_data = {
            "nom": "ACME Corp",
            "type": "entreprise",
            "secteur_activite": "Informatique",
            "zip_code": "75001",
            "city": "Paris",
            "contact_nom": "Jean Dupont",
            "contact_email": "jean.dupont@acme.fr",
            "contact_telephone": "0601020303",
            "website": "https://acme.fr",
        }

    def test_serializer_valid_data(self):
        serializer = PartenaireSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_serializer_missing_nom(self):
        data = self.valid_data.copy()
        data.pop("nom")
        serializer = PartenaireSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("nom", serializer.errors)

    def test_serializer_invalid_zip(self):
        data = self.valid_data.copy()
        data["zip_code"] = "75A01"
        serializer = PartenaireSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("zip_code", serializer.errors)

    def test_serializer_invalid_phone(self):
        data = self.valid_data.copy()
        data["contact_telephone"] = "12345"
        serializer = PartenaireSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("contact_telephone", serializer.errors)

    def test_serializer_output_format(self):
        partenaire = Partenaire.objects.create(**self.valid_data)
        serializer = PartenaireSerializer(instance=partenaire)
        output = serializer.data
        self.assertIn("success", output)
        self.assertIn("message", output)
        self.assertIn("data", output)
        self.assertTrue(output["success"])
        self.assertIsInstance(output["data"], dict)
