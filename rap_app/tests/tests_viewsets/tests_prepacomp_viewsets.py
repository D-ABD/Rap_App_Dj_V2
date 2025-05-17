from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.contenttypes.models import ContentType
from datetime import date, timedelta

from ...models.custom_user import CustomUser
from ...models.centres import Centre
from ...models.prepacomp import Semaine, PrepaCompGlobal
from ...models.logs import LogUtilisateur


class BaseAuthenticatedTestCase(APITestCase):
    def setUp(self):
        self.password = "Test1234!"
        self.user = CustomUser.objects.create_user(
            email="admin@example.com",
            username="admin",
            password=self.password,
            role=CustomUser.ROLE_ADMIN,
            is_staff=True
        )
        self.centre = Centre.objects.create(nom="Centre Test")
        self.refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.refresh.access_token}")


class SemaineViewSetTest(BaseAuthenticatedTestCase):

    def setUp(self):
        super().setUp()
        self.url_list = reverse("semaine-list")
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

    def test_create_semaine(self):
        response = self.client.post(self.url_list, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])

    def test_create_invalid_sum_departements(self):
        data = self.valid_data.copy()
        data["departements"] = {"75": 5, "92": 5}
        response = self.client.post(self.url_list, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("departements", response.data)

    def test_update_semaine(self):
        semaine = Semaine.objects.create(
            centre=self.centre,
            annee=2025,
            mois=5,
            numero_semaine=20,
            date_debut_semaine=date(2025, 5, 12),
            date_fin_semaine=date(2025, 5, 18),
            objectif_annuel_prepa=200,
            objectif_mensuel_prepa=80,
            objectif_hebdo_prepa=20,
            nombre_places_ouvertes=15,
            nombre_prescriptions=18,
            nombre_presents_ic=15,
            nombre_adhesions=12,
            departements={"75": 6, "92": 6},
            nombre_par_atelier={"AT1": 6, "AT3": 6}
        )
        url = reverse("semaine-detail", args=[semaine.id])
        response = self.client.patch(url, {
            "objectif_hebdo_prepa": 12,
            "nombre_adhesions": 12,
            "nombre_presents_ic": 15,
            "departements": {"75": 6, "92": 6},
            "date_debut_semaine": "2025-05-12",
            "date_fin_semaine": "2025-05-18"
        }, format="json")
        print(">>>> PATCH erreur : ", response.status_code, response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["objectifs"]["hebdomadaire"], 12)

    def test_list_semaines(self):
        Semaine.objects.create(centre=self.centre, **{k: v for k, v in self.valid_data.items() if k != "centre"})
        response = self.client.get(self.url_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn("results", response.data["data"])

    def test_delete_semaine(self):
        semaine = Semaine.objects.create(centre=self.centre, **{k: v for k, v in self.valid_data.items() if k != "centre"})
        url = reverse("semaine-detail", args=[semaine.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        semaine.refresh_from_db()
        self.assertFalse(semaine.is_active)

    def test_courante_action(self):
        Semaine.create_for_week(self.centre, date.today())
        response = self.client.get(reverse("semaine-courante") + f"?centre_id={self.centre.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])


class PrepaCompGlobalViewSetTest(BaseAuthenticatedTestCase):

    def setUp(self):
        super().setUp()
        self.url_list = reverse("prepa-global-list")
        self.data = {
            "centre": self.centre.id,
            "annee": 2025,
            "adhesions": 100,
            "total_presents": 120,
            "total_prescriptions": 150,
            "total_places_ouvertes": 130,
            "objectif_annuel_prepa": 200,
            "objectif_hebdomadaire_prepa": 20,
            "objectif_annuel_jury": 40,
            "objectif_mensuel_jury": 10
        }

    def test_create_prepa_global(self):
        response = self.client.post(self.url_list, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])

        log = LogUtilisateur.objects.filter(
            content_type=ContentType.objects.get_for_model(PrepaCompGlobal),
            object_id=response.data["data"]["id"],
            action__icontains="création",
            created_by=self.user
        )
        self.assertTrue(log.exists())

    def test_list_prepa_globaux(self):
        PrepaCompGlobal.objects.create(centre=self.centre, **{k: v for k, v in self.data.items() if k != "centre"})
        response = self.client.get(self.url_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])

    def test_update_prepa_global(self):
        obj = PrepaCompGlobal.objects.create(centre=self.centre, **{k: v for k, v in self.data.items() if k != "centre"})
        url = reverse("prepa-global-detail", args=[obj.id])
        response = self.client.patch(url, {"objectif_annuel_prepa": 250})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["objectif_annuel_prepa"], 250)

    def test_delete_prepa_global(self):
        obj = PrepaCompGlobal.objects.create(centre=self.centre, **{k: v for k, v in self.data.items() if k != "centre"})
        url = reverse("prepa-global-detail", args=[obj.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        obj.refresh_from_db()
        self.assertFalse(obj.is_active)

    def test_par_centre_action(self):
        PrepaCompGlobal.objects.create(centre=self.centre, **{k: v for k, v in self.data.items() if k != "centre"})
        url = reverse("prepa-global-par-centre") + f"?centre_id={self.centre.id}&annee=2025"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
