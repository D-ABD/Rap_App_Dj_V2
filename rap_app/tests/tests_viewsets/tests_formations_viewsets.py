from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from datetime import date

from ...models.custom_user import CustomUser
from ...models.centres import Centre
from ...models.vae_jury import VAE, SuiviJury, HistoriqueStatutVAE


class SuiviJuryViewSetTest(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="jury@test.com",
            username="jury_user",
            password="pass",
            is_staff=True,
            role=CustomUser.ROLE_ADMIN
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.centre = Centre.objects.create(nom="Centre Test")
        self.url = reverse("suivijury-list")

    def test_create_suivi_jury(self):
        data = {
            "centre_id": self.centre.pk,
            "annee": 2024,
            "mois": 5,
            "objectif_jury": 10,
            "jurys_realises": 8
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])


class VAEViewSetTest(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="vae@test.com",
            username="vae_user",
            password="pass",
            is_staff=True,
            role=CustomUser.ROLE_ADMIN
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.centre = Centre.objects.create(nom="Centre VAE")
        self.url = reverse("vae-list")

    def test_create_vae(self):
        data = {
            "centre_id": self.centre.pk,
            "statut": "accompagnement",
            "commentaire": "Test commentaire"
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["success"], True)


class HistoriqueStatutVAEViewSetTest(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="hist@test.com",
            username="hist_user",
            password="pass",
            is_staff=True,
            role=CustomUser.ROLE_ADMIN
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.centre = Centre.objects.create(nom="Centre Hist")
        self.vae = VAE.objects.create(centre=self.centre, statut="info", created_by=self.user)

        HistoriqueStatutVAE.objects.create(
            vae=self.vae,
            statut="info",
            date_changement_effectif=date.today(),
            commentaire="Création initiale",
            created_by=self.user
        )
        self.url = reverse("historiquestatutvae-list")

    def test_list_historiques(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
