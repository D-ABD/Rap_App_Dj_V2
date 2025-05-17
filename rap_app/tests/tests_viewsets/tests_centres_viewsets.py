from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from ...models.centres import Centre
from ...models.custom_user import CustomUser

class CentreViewSetTestCase(APITestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            email="admin@example.com",
            password="adminpass",
            role="admin"
        )
        self.client.force_authenticate(user=self.admin)
        self.list_url = reverse("centre-list")

    def test_create_centre_success(self):
        data = {"nom": "Nouveau Centre", "code_postal": "75015"}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["nom"], "Nouveau Centre")

    def test_create_centre_invalid(self):
        data = {"nom": "", "code_postal": "7501"}  # Invalid
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_centres(self):
        Centre.objects.create(nom="Centre A", code_postal="75001")
        Centre.objects.create(nom="Centre B", code_postal="75002")
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertGreaterEqual(len(response.data["data"]["results"]), 2)

    def test_update_centre(self):
        centre = Centre.objects.create(nom="Modifiable", code_postal="75010")
        url = reverse("centre-detail", args=[centre.pk])
        data = {"nom": "Modifié", "code_postal": "75011"}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["nom"], "Modifié")

    def test_delete_centre(self):
        centre = Centre.objects.create(nom="À Supprimer", code_postal="75012")
        url = reverse("centre-detail", args=[centre.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Centre.objects.filter(pk=centre.pk).count(), 0)
