from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.contenttypes.models import ContentType
from datetime import date, timedelta

from ...models.custom_user import CustomUser
from ...models.centres import Centre
from ...models.formations import Formation
from ...models.rapports import Rapport
from ...models.logs import LogUtilisateur
from ...models.statut import Statut
from ...models.types_offre import TypeOffre

class RapportViewSetTestCase(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="rapport@test.com",
            username="testuser",
            password="testpass",
            is_staff=True,
            role=CustomUser.ROLE_ADMIN
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.centre = Centre.objects.create(nom="Centre Test", created_by=self.user)
        self.type_offre = TypeOffre.objects.create(nom="non_defini", created_by=self.user)
        self.statut = Statut.objects.create(nom="non_defini", created_by=self.user)
        self.formation = Formation.objects.create(
            nom="Formation A",
            centre=self.centre,
            type_offre=self.type_offre,
            statut=self.statut,
            created_by=self.user
        )

        self.rapport = Rapport.objects.create(
            nom="Rapport Initial",
            type_rapport=Rapport.TYPE_OCCUPATION,
            periode=Rapport.PERIODE_MENSUEL,
            date_debut=date.today() - timedelta(days=30),
            date_fin=date.today(),
            format=Rapport.FORMAT_PDF,
            centre=self.centre,
            type_offre=self.type_offre,
            statut=self.statut,
            formation=self.formation,
            donnees={"initial": True},
            temps_generation=2.5,
            created_by=self.user
        )

        self.list_url = reverse("rapport-list")
        self.detail_url = reverse("rapport-detail", args=[self.rapport.id])

    def test_list_rapports(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn("results", response.data["data"])

    def test_retrieve_rapport(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["id"], self.rapport.id)
        self.assertEqual(response.data["data"]["nom"], self.rapport.nom)

    def test_create_rapport(self):
        data = {
            "nom": "Rapport Créé",
            "type_rapport": Rapport.TYPE_UTILISATEUR,
            "periode": Rapport.PERIODE_HEBDOMADAIRE,
            "date_debut": date.today() - timedelta(days=6),
            "date_fin": date.today(),
            "format": Rapport.FORMAT_HTML,
            "centre": self.centre.id,
            "type_offre": self.type_offre.id,
            "statut": self.statut.id,
            "formation": self.formation.id,
            "donnees": {"nb": 5},
            "temps_generation": 1.2
        }
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])

        rapport_id = response.data["data"]["id"]
        log = LogUtilisateur.objects.filter(
            content_type=ContentType.objects.get_for_model(Rapport),
            object_id=rapport_id,
            action="création",
            created_by=self.user
        )
        self.assertTrue(log.exists(), "Log de création manquant")

    def test_update_rapport(self):
        url = reverse("rapport-detail", args=[self.rapport.id])
        data = {"nom": "Rapport Modifié"}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["nom"], "Rapport Modifié")

        log = LogUtilisateur.objects.filter(
            content_type=ContentType.objects.get_for_model(Rapport),
            object_id=self.rapport.pk,
            action="modification",
            created_by=self.user
        )
        self.assertTrue(log.exists(), "Log de modification manquant")

    def test_delete_rapport(self):
        url = reverse("rapport-detail", args=[self.rapport.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.rapport.refresh_from_db()
        self.assertFalse(self.rapport.is_active)

        log = LogUtilisateur.objects.filter(
            content_type=ContentType.objects.get_for_model(Rapport),
            object_id=self.rapport.pk,
            action="suppression",
            created_by=self.user
        )
        self.assertTrue(log.exists(), "Log de suppression manquant")

    def test_validation_dates_invalides(self):
        data = {
            "nom": "Rapport Invalide",
            "type_rapport": Rapport.TYPE_STATUT,
            "periode": Rapport.PERIODE_MENSUEL,
            "date_debut": date.today(),
            "date_fin": date.today() - timedelta(days=10),
            "format": Rapport.FORMAT_PDF
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("date_debut", response.data)
        self.assertIn("date_fin", response.data)

    def test_permission_required(self):
        self.client.logout()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
