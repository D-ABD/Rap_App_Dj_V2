from django.test import TestCase
from datetime import date, timedelta
from ...models.prepacomp import Semaine, PrepaCompGlobal
from ...models.centres import Centre
from ...api.serializers.prepacomp_serializers import SemaineSerializer, PrepaCompGlobalSerializer


class SemaineSerializerTestCase(TestCase):
    def setUp(self):
        self.centre = Centre.objects.create(nom="Test Centre")
        self.valid_data = {
            "centre": self.centre.id,
            "annee": 2025,
            "mois": 5,
            "numero_semaine": 20,
            "date_debut_semaine": date(2025, 5, 12),
            "date_fin_semaine": date(2025, 5, 18),
            "objectif_annuel_prepa": 200,
            "objectif_mensuel_prepa": 80,
            "objectif_hebdo_prepa": 20,
            "nombre_places_ouvertes": 15,
            "nombre_prescriptions": 18,
            "nombre_presents_ic": 14,
            "nombre_adhesions": 12,
            "departements": {"75": 5, "92": 7},
            "nombre_par_atelier": {"AT1": 6, "AT3": 6}
        }

    def test_serializer_valid_data(self):
        """✅ Vérifie que les données valides passent"""
        serializer = SemaineSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_serializer_invalid_departement_code(self):
        """❌ Vérifie l’échec si un département est invalide"""
        data = self.valid_data.copy()
        data["departements"] = {"99": 5}
        serializer = SemaineSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("departements", serializer.errors)

    def test_serializer_sum_departements_mismatch(self):
        """❌ Vérifie que la somme des départements doit égaler les adhésions"""
        data = self.valid_data.copy()
        data["departements"] = {"75": 5, "92": 5}  # total = 10, attendu = 12
        serializer = SemaineSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("departements", serializer.errors)

    def test_serializer_invalid_objectif_hebdo(self):
        """❌ Vérifie que l’objectif hebdo ne dépasse pas la limite"""
        data = self.valid_data.copy()
        data["objectif_hebdo_prepa"] = 10000  # dépasse MAX_OBJECTIF
        serializer = SemaineSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("objectif_hebdo_prepa", serializer.errors)

    def test_to_representation_output_structure(self):
        """✅ Structure de sortie avec success/message/data"""
        semaine = Semaine.objects.create(
            centre=self.centre,
            **{k: v for k, v in self.valid_data.items() if k != "centre"}
        )
        serializer = SemaineSerializer(instance=semaine)
        output = serializer.data
        self.assertTrue(output["success"])
        self.assertIn("message", output)
        self.assertIn("data", output)
        self.assertEqual(output["data"]["annee"], self.valid_data["annee"])


class PrepaCompGlobalSerializerTestCase(TestCase):
    def setUp(self):
        self.centre = Centre.objects.create(nom="Centre Global")
        self.instance = PrepaCompGlobal.objects.create(
            centre=self.centre,
            annee=2025,
            adhesions=120,
            total_presents=150,
            total_prescriptions=180,
            total_places_ouvertes=130,
            objectif_annuel_prepa=200,
            objectif_hebdomadaire_prepa=20,
            objectif_annuel_jury=40,
            objectif_mensuel_jury=10,
        )

    def test_to_representation_structure(self):
        """✅ Structure de sortie enrichie avec taux et objectifs"""
        serializer = PrepaCompGlobalSerializer(instance=self.instance)
        data = serializer.data
        self.assertTrue(data["success"])
        self.assertIn("data", data)
        self.assertEqual(data["data"]["annee"], 2025)
        self.assertIn("taux_transformation", data["data"])
        self.assertIn("objectif_jury", data["data"])

    def test_taux_transformation_coherence(self):
        """✅ Vérifie le taux de transformation calculé"""
        taux = round((120 / 150) * 100, 1)
        self.assertAlmostEqual(self.instance.taux_transformation(), taux)
