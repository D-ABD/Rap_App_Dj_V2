from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from ...models.custom_user import CustomUser
from ...models.centres import Centre
from ...models.logs import LogUtilisateur


class LogUtilisateurViewSetTestCase(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="log@test.com",
            username="loguser",
            password="pass",
            is_staff=True,
            role=CustomUser.ROLE_ADMIN
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.centre = Centre.objects.create(nom="Centre log", created_by=self.user)
        self.log = LogUtilisateur.log_action(
            instance=self.centre,
            action=LogUtilisateur.ACTION_CREATE,
            user=self.user,
            details="Création test"
        )

        self.list_url = reverse("logutilisateur-list")
        self.detail_url = reverse("logutilisateur-detail", args=[self.log.pk])

    def test_list_logs_success_structure(self):
        """
        ✅ Liste des logs avec structure complète : success, message, data
        """
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["message"], "Liste paginée des résultats.")
        self.assertIn("data", response.data)
        self.assertIn("results", response.data["data"])
        self.assertGreaterEqual(response.data["data"]["count"], 1)

    def test_retrieve_log_success_structure(self):
        """
        ✅ Détail d’un log avec structure complète
        """
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["message"], "Log utilisateur récupéré avec succès.")
        self.assertIn("data", response.data)
        self.assertEqual(response.data["data"]["id"], self.log.pk)
        self.assertEqual(response.data["data"]["user"], self.user.username)

    def test_post_not_allowed(self):
        """
        🚫 Méthode POST non autorisée sur les logs
        """
        response = self.client.post(self.list_url, {"action": "test"})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_not_allowed(self):
        """
        🚫 Méthode DELETE non autorisée sur les logs
        """
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_permissions_required(self):
        """
        🚫 Accès refusé sans authentification
        """
        self.client.logout()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
