from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.urls import reverse
from ...models.custom_user import CustomUser
from ...models.statut import Statut


class StatutViewSetTestCase(APITestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            email="admin@example.com",
            username="admin",
            password="StrongPass123",
            role=CustomUser.ROLE_ADMIN,
            is_staff=True
        )
        token = RefreshToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(token.access_token)}")
        self.list_url = reverse("statut-list")

    def test_create_statut_success(self):
        data = {"nom": Statut.PLEINE, "couleur": "#123456"}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["nom"], Statut.PLEINE)

    def test_create_statut_autre_without_description(self):
        data = {"nom": Statut.AUTRE, "couleur": "#FF0000"}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("description_autre", response.data)

    def test_create_statut_invalid_color(self):
        data = {"nom": Statut.PLEINE, "couleur": "bleu"}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("couleur", response.data)

    def test_list_statuts(self):
        Statut.objects.create(nom=Statut.PLEINE, couleur="#111111")
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn("data", response.data)

    def test_retrieve_statut(self):
        statut = Statut.objects.create(nom=Statut.QUASI_PLEINE, couleur="#333333")
        url = reverse("statut-detail", args=[statut.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["nom"], Statut.QUASI_PLEINE)

    def test_update_statut(self):
        statut = Statut.objects.create(nom=Statut.RECRUTEMENT_EN_COURS, couleur="#222222")
        url = reverse("statut-detail", args=[statut.id])
        data = {"nom": Statut.FORMATION_EN_COURS, "couleur": "#00FF00"}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["couleur"], "#00FF00")

    def test_partial_update_statut(self):
        statut = Statut.objects.create(nom=Statut.RECRUTEMENT_EN_COURS, couleur="#ABCDEF")
        url = reverse("statut-detail", args=[statut.id])
        data = {"couleur": "#123ABC"}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["couleur"], "#123ABC")

    def test_delete_statut_sets_is_active_false(self):
        statut = Statut.objects.create(nom=Statut.NON_DEFINI, couleur="#999999")
        url = reverse("statut-detail", args=[statut.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        statut.refresh_from_db()
        self.assertFalse(statut.is_active)

    def test_badge_html_display(self):
        statut = Statut.objects.create(nom=Statut.PLEINE, couleur="#000000")
        badge = statut.get_badge_html()
        self.assertIn('<span', badge)
        self.assertIn('style="background-color:#000000;', badge)

    def test_csv_row_and_headers(self):
        statut = Statut.objects.create(nom=Statut.PLEINE, couleur="#123456")
        csv_row = statut.to_csv_row()
        headers = Statut.get_csv_headers()
        fields = Statut.get_csv_fields()
        self.assertEqual(len(csv_row), len(headers))
        self.assertEqual(len(csv_row), len(fields))
