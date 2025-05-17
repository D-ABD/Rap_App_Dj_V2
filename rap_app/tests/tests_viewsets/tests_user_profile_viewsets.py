from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.contenttypes.models import ContentType
from ...models.custom_user import CustomUser
from ...models.logs import LogUtilisateur


class CustomUserViewSetTestCase(APITestCase):
    def setUp(self):
        self.password = "StrongPass123"
        self.user = CustomUser.objects.create_user(
            email="admin@example.com",
            username="admin",
            password=self.password,
            role=CustomUser.ROLE_ADMIN,
            is_staff=True
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        self.list_url = reverse("user-list")
        self.me_url = reverse("user-me")
        self.roles_url = reverse("user-roles")

    def test_list_users(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("data", response.data)
        self.assertTrue(response.data["success"])

    def test_create_user(self):
        data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "role": "stagiaire",
            "phone": "0606060606"
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["email"], data["email"])

        # Vérification du log de création
        created_user_id = response.data["data"]["id"]
        log = LogUtilisateur.objects.filter(
            content_type=ContentType.objects.get_for_model(CustomUser),
            object_id=created_user_id,
            action__icontains="création",
            created_by=self.user
        )
        self.assertTrue(log.exists(), "Log de création non détecté.")

    def test_retrieve_user(self):
        response = self.client.get(reverse("user-detail", args=[self.user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["email"], self.user.email)

    def test_update_user(self):
        url = reverse("user-detail", args=[self.user.id])
        data = {"first_name": "Modifié"}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["first_name"], "Modifié")

        # Vérification du log de modification
        log = LogUtilisateur.objects.filter(
            content_type=ContentType.objects.get_for_model(CustomUser),
            object_id=self.user.pk,
            action__icontains="modification",
            created_by=self.user
        )
        self.assertTrue(log.exists(), "Log de modification non détecté.")

    def test_delete_user_sets_is_active_false(self):
        url = reverse("user-detail", args=[self.user.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

        # Vérification du log de suppression
        log = LogUtilisateur.objects.filter(
            content_type=ContentType.objects.get_for_model(CustomUser),
            object_id=self.user.pk,
            action__icontains="suppression",
            created_by=self.user
        )
        self.assertTrue(log.exists(), "Log de suppression non détecté.")

    def test_me_endpoint(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["email"], self.user.email)

    def test_roles_endpoint(self):
        response = self.client.get(self.roles_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("stagiaire", response.data["data"])
        self.assertTrue(response.data["success"])
