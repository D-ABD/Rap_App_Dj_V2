# tests/test_typeoffre_serializers.py

from django.test import TestCase
from django.core.exceptions import ValidationError

from ...api.serializers.types_offre_serializers import TypeOffreSerializer
from ...models.types_offre import TypeOffre


class TypeOffreSerializerTestCase(TestCase):
    def setUp(self):
        self.valid_data = {
            "nom": TypeOffre.CRIF,
            "autre": "",
            "couleur": "#123456",
        }

    def test_serializer_valid_data(self):
        """
        ✅ Vérifie que le serializer accepte des données valides.
        """
        serializer = TypeOffreSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_serializer_output_structure(self):
        """
        ✅ Vérifie la structure du `to_representation()`
        """
        type_offre = TypeOffre.objects.create(**self.valid_data)
        serializer = TypeOffreSerializer(instance=type_offre)
        output = serializer.data
        self.assertIn("success", output)
        self.assertIn("message", output)
        self.assertIn("data", output)
        self.assertEqual(output["data"]["nom"], "crif")

    def test_serializer_autre_required_if_nom_autre(self):
        """
        ❌ Vérifie que le champ `autre` est requis si `nom` == "autre"
        """
        data = {
            "nom": TypeOffre.AUTRE,
            "autre": "",  # manquant
            "couleur": "#20c997"
        }
        serializer = TypeOffreSerializer(data=data)
        self.assertTrue(serializer.is_valid())  # ✅ valide syntaxiquement
        with self.assertRaises(ValidationError) as context:
            serializer.save()  # ❌ déclenche la validation métier du modèle

        self.assertIn("autre", context.exception.message_dict)


    def test_serializer_invalid_color_format(self):
        """
        ❌ Vérifie qu'un code couleur invalide est rejeté
        """
        data = self.valid_data.copy()
        data["couleur"] = "rouge"
        serializer = TypeOffreSerializer(data=data)
        self.assertTrue(serializer.is_valid())  # ✅ syntaxiquement OK
        with self.assertRaises(ValidationError) as context:
            serializer.save()  # ❌ déclenche la validation `clean()`

        self.assertIn("couleur", context.exception.message_dict)

    def test_serializer_autre_valide(self):
        data = {
            "nom": TypeOffre.AUTRE,
            "autre": "Test personnalisé",
            "couleur": "#20c997"
        }
        serializer = TypeOffreSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        instance = serializer.save()
        self.assertEqual(instance.nom, TypeOffre.AUTRE)
        self.assertEqual(instance.autre, "Test personnalisé")

    def test_serializer_autre_unique_constraint(self):
        TypeOffre.objects.create(nom=TypeOffre.AUTRE, autre="Doublon", couleur="#123456")
        data = {
            "nom": TypeOffre.AUTRE,
            "autre": "Doublon",  # même nom personnalisé
            "couleur": "#123456"
        }
        serializer = TypeOffreSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        with self.assertRaises(ValidationError):
            serializer.save()
