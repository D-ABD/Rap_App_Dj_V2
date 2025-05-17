from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.contenttypes.models import ContentType
from datetime import date
from django.utils import timezone

from ...models.custom_user import CustomUser
from ...models.centres import Centre
from ...models.vae_jury import VAE, SuiviJury, HistoriqueStatutVAE
from ...models.logs import LogUtilisateur

from django.contrib.auth import get_user_model

User = get_user_model()

class BaseAPITestCase(APITestCase):
    def setUp(self):
        self.password = "StrongPassword123"
        self.user = CustomUser.objects.create_user(
            email="admin@example.com",
            username="admin",
            password=self.password,
            role=CustomUser.ROLE_ADMIN,
            is_staff=True
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
        self.centre = Centre.objects.create(nom="Centre Principal")

class SuiviJuryViewSetTest(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("suivijury-list")

    def test_create_suivi_jury(self):
        data = {
            "centre_id": self.centre.id,  # <-- au lieu de "centre"
            "annee": 2024,
            "mois": 5,
            "objectif_jury": 10,
            "jurys_realises": 8
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["objectif_jury"], 10)

        obj_id = response.data["data"]["id"]
        log = LogUtilisateur.objects.filter(
            content_type=ContentType.objects.get_for_model(SuiviJury),
            object_id=obj_id,
            action__icontains="création",
            created_by=self.user
        )
        self.assertTrue(log.exists())

    def test_update_suivi_jury(self):
        obj = SuiviJury.objects.create(centre=self.centre, annee=2024, mois=5)
        url = reverse("suivijury-detail", args=[obj.id])
        response = self.client.patch(url, {"objectif_jury": 20})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["objectif_jury"], 20)

    def test_delete_suivi_jury(self):
        obj = SuiviJury.objects.create(centre=self.centre, annee=2024, mois=5)
        url = reverse("suivijury-detail", args=[obj.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        obj.refresh_from_db()
        self.assertFalse(obj.is_active)

class VAEViewSetTest(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("vae-list")

    def test_create_vae(self):
        data = {
            "centre_id": self.centre.id,  # <-- au lieu de "centre"
            "statut": "accompagnement",
            "commentaire": "Phase d'accompagnement"
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])

    def test_update_vae(self):
        obj = VAE.objects.create(centre=self.centre, statut="info")
        url = reverse("vae-detail", args=[obj.id])
        response = self.client.patch(url, {"statut": "jury"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["statut"], "jury")

    def test_changer_statut(self):
        obj = VAE.objects.create(centre=self.centre, statut="info")
        url = reverse("vae-changer-statut", args=[obj.id])
        data = {"statut": "jury", "date_changement_effectif": str(date.today()), "commentaire": "Prévu"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["statut"], "jury")

    def test_historiques(self):
        obj = VAE.objects.create(centre=self.centre, statut="accompagnement")
        HistoriqueStatutVAE.objects.create(
            vae=obj,
            statut="accompagnement",
            date_changement_effectif=date.today(),
            commentaire="Début accompagnement"
        )
        url = reverse("vae-historiques", args=[obj.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["data"]), 1)

class HistoriqueStatutVAEViewSetTest(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.vae = VAE.objects.create(centre=self.centre, statut="info", created_by=self.user)
        HistoriqueStatutVAE.objects.create(
            vae=self.vae,
            statut="info",
            date_changement_effectif=timezone.now().date(),
            commentaire="Initial",
            created_by=self.user
        )
        self.url = reverse("historiquestatutvae-list")

    def test_list_historiques(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["success"], True)