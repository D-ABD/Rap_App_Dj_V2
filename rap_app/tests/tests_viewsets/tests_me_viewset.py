from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from ...models.custom_user import CustomUser
from ...models.logs import LogUtilisateur
from django.contrib.contenttypes.models import ContentType


class MeAPIViewTestCase(APITestCase):
    def setUp(self):
        self.password = "StrongPass123"
        self.user = CustomUser.objects.create_user(
            email="user@example.com",
            username="user",
            password=self.password,
            role=CustomUser.ROLE_STAGIAIRE
        )
        self.client.login(email=self.user.email, password=self.password)
        self.url = reverse("me-profile")

    def test_get_own_profile_authenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("data", response.data)
        self.assertEqual(response.data["data"]["email"], self.user.email)
        self.assertTrue(response.data["success"])

    def test_patch_own_profile(self):
        data = {"first_name": "Modifié", "phone": "0102030405"}
        response = self.client.patch(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["first_name"], "Modifié")
        self.assertEqual(response.data["data"]["phone"], "0102030405")
        self.assertTrue(response.data["success"])

    def test_patch_creates_log_entry(self):
        """✅ Vérifie qu'une mise à jour du profil génère un log utilisateur."""
        data = {"first_name": "LogTest"}
        response = self.client.patch(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        logs = LogUtilisateur.objects.filter(
            content_type=ContentType.objects.get_for_model(CustomUser),
            object_id=self.user.pk,
            action__icontains="modification",
            created_by=self.user
        )
        self.assertTrue(logs.exists(), "Aucun log utilisateur de modification détecté.")

    def test_unauthenticated_access_denied(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
