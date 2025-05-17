from django.test import TestCase
from datetime import date, timedelta
from ...models.custom_user import CustomUser
from ...models.centres import Centre
from ...models.formations import Formation
from ...models.types_offre import TypeOffre
from ...models.statut import Statut
from ...models.rapports import Rapport
from ...api.serializers.rapports_serializers import RapportSerializer


class RapportSerializerTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="test@rapport.com",
            username="rapporteur",
            password="password",
            role=CustomUser.ROLE_ADMIN,
            is_staff=True
        )
        self.centre = Centre.objects.create(nom="Centre Test", created_by=self.user)
        self.type_offre = TypeOffre.objects.create(nom="non_defini", created_by=self.user)
        self.statut = Statut.objects.create(nom="non_defini", created_by=self.user)
        self.formation = Formation.objects.create(
            nom="Formation X",
            centre=self.centre,
            type_offre=self.type_offre,
            statut=self.statut,
            created_by=self.user
        )
        self.rapport = Rapport.objects.create(
            nom="Rapport test",
            type_rapport=Rapport.TYPE_OCCUPATION,
            periode=Rapport.PERIODE_MENSUEL,
            date_debut=date.today() - timedelta(days=30),
            date_fin=date.today(),
            format=Rapport.FORMAT_PDF,
            centre=self.centre,
            type_offre=self.type_offre,
            statut=self.statut,
            formation=self.formation,
            donnees={"total": 42},
            temps_generation=3.21,
            created_by=self.user
        )

    def test_serializer_output_structure(self):
        """
        ✅ Vérifie que la sortie respecte success/message/data
        """
        serializer = RapportSerializer(instance=self.rapport)
        output = serializer.data
        self.assertTrue(output["success"])
        self.assertEqual(output["message"], "Rapport récupéré avec succès.")
        self.assertIn("data", output)


    def test_serializer_validation_dates_inverses(self):
        """
        ❌ Test d’erreur si date_debut > date_fin
        """
        invalid_data = {
            "nom": "Erreur",
            "type_rapport": Rapport.TYPE_STATUT,
            "periode": Rapport.PERIODE_MENSUEL,
            "date_debut": date.today(),
            "date_fin": date.today() - timedelta(days=1),
            "format": Rapport.FORMAT_PDF,
        }
        serializer = RapportSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("date_debut", serializer.errors)
        self.assertIn("date_fin", serializer.errors)

    def test_display_fields(self):
        """
        ✅ Vérifie les champs *_display et *_nom
        """
        serializer = RapportSerializer(instance=self.rapport)
        data = serializer.data["data"]
        self.assertEqual(data["type_rapport_display"], "Rapport d'occupation des formations")
        self.assertEqual(data["periode_display"], "Mensuel")
        self.assertEqual(data["format_display"], "PDF")
        self.assertEqual(data["centre_nom"], "Centre Test")
        self.assertEqual(data["formation_nom"], "Formation X")
