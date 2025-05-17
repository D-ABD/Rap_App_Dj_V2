
from django.test import TestCase
from datetime import date
from ...models.vae_jury import VAE, SuiviJury, HistoriqueStatutVAE
from ...models.custom_user import CustomUser
from ...models.centres import Centre
from ...api.serializers.vae_jury_serializers import (
    VAESerializer, SuiviJurySerializer, ChangerStatutVAESerializer, HistoriqueStatutVAESerializer
)


class VAESerializerTestCase(TestCase):
    def setUp(self):
        self.centre = Centre.objects.create(nom="Centre Test")
        self.user = CustomUser.objects.create_user(
            email="test@example.com", username="testuser", password="pass", role="admin"
        )

    def test_valid_serializer(self):
        data = {
            "centre_id": self.centre.id,
            "statut": "accompagnement",
            "commentaire": "En cours"
        }
        serializer = VAESerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_default_statut_set(self):
        data = {
            "centre_id": self.centre.id,
            "commentaire": "Sans statut explicite"
        }
        serializer = VAESerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["statut"], "info")

    def test_invalid_statut(self):
        data = {
            "centre_id": self.centre.id,
            "statut": "invalide"
        }
        serializer = VAESerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("statut", serializer.errors)


class SuiviJurySerializerTestCase(TestCase):
    def setUp(self):
        self.centre = Centre.objects.create(nom="Centre Jury")

    def test_valid_suivi_jury(self):
        data = {
            "centre_id": self.centre.id,
            "annee": 2024,
            "mois": 5,
            "objectif_jury": 10,
            "jurys_realises": 8
        }
        serializer = SuiviJurySerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_mois_out_of_range(self):
        data = {
            "centre_id": self.centre.id,
            "annee": 2024,
            "mois": 13,
            "objectif_jury": 5,
            "jurys_realises": 2
        }
        serializer = SuiviJurySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("mois", serializer.errors)


class ChangerStatutVAESerializerTestCase(TestCase):
    def test_valid_statut_change(self):
        data = {
            "statut": "jury",
            "date_changement_effectif": "2024-04-01",
            "commentaire": "Prévu pour le jury"
        }
        serializer = ChangerStatutVAESerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_invalid_statut(self):
        data = {
            "statut": "nonexistent"
        }
        serializer = ChangerStatutVAESerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("statut", serializer.errors)


class HistoriqueStatutVAESerializerTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="strongpass123",
            role=CustomUser.ROLE_ADMIN
        )
        self.centre = Centre.objects.create(nom="Centre test")

        # Création manuelle de la VAE + save avec user
        self.vae = VAE(centre=self.centre, statut="info")
        self.vae.save(user=self.user)

        # Création manuelle de l’historique + save avec user
        self.historique = HistoriqueStatutVAE(
            vae=self.vae,
            statut="info",
            date_changement_effectif=date.today(),
            commentaire="Début du parcours"
        )
        self.historique.save(user=self.user)

    def test_serializer_output(self):
        """
        ✅ Vérifie que le serializer retourne le format structuré attendu
        """
        serializer = HistoriqueStatutVAESerializer(instance=self.historique)
        output = serializer.data

        self.assertIn("id", output)
        self.assertIn("vae_id", output)
        self.assertEqual(output["statut"], "info")
        self.assertEqual(output["statut_libelle"], "Demande d'informations")
        self.assertEqual(output["vae_reference"], self.vae.reference)