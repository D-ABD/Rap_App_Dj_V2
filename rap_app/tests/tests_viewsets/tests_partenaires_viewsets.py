# tests/test_partenaire_viewsets.py

from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.contenttypes.models import ContentType

from ...models.custom_user import CustomUser
from ...models.partenaires import Partenaire
from ...models.logs import LogUtilisateur


class PartenaireViewSetTestCase(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="admin@example.com",
            username="admin",
            password="StrongPass123",
            role=CustomUser.ROLE_ADMIN,
            is_staff=True
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        self.list_url = reverse("partenaire-list")
        self.valid_data = {
            "nom": "ACME Corp",
            "type": "entreprise",
            "secteur_activite": "Informatique",
            "zip_code": "75001",
            "city": "Paris",
            "contact_nom": "Jean Dupont",
            "contact_email": "jean.dupont@acme.fr",
            "contact_telephone": "0601020303",
            "website": "https://acme.fr"
        }

    def test_create_partenaire(self):
        response = self.client.post(self.list_url, self.valid_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["nom"], self.valid_data["nom"])

        partenaire_id = response.data["data"]["id"]
        log = LogUtilisateur.objects.filter(
            content_type=ContentType.objects.get_for_model(Partenaire),
            object_id=partenaire_id,
            action__icontains="création",
            created_by=self.user
        )
        self.assertTrue(log.exists(), "Log de création manquant.")

    def test_list_partenaires(self):
        Partenaire.objects.create(**self.valid_data)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertGreaterEqual(len(response.data["data"]["results"]), 1)

    def test_retrieve_partenaire(self):
        partenaire = Partenaire.objects.create(**self.valid_data)
        url = reverse("partenaire-detail", args=[partenaire.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["id"], partenaire.id)

    def test_update_partenaire(self):
        partenaire = Partenaire.objects.create(**self.valid_data)
        url = reverse("partenaire-detail", args=[partenaire.id])
        patch = {"city": "Lyon"}
        response = self.client.patch(url, patch)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["localisation"]["ville"], "Lyon")

        log = LogUtilisateur.objects.filter(
            content_type=ContentType.objects.get_for_model(Partenaire),
            object_id=partenaire.id,
            action__icontains="modification",
            created_by=self.user
        )
        self.assertTrue(log.exists(), "Log de modification manquant.")

    def test_delete_partenaire(self):
        partenaire = Partenaire.objects.create(**self.valid_data)
        url = reverse("partenaire-detail", args=[partenaire.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        partenaire.refresh_from_db()
        self.assertFalse(partenaire.is_active)

        log = LogUtilisateur.objects.filter(
            content_type=ContentType.objects.get_for_model(Partenaire),
            object_id=partenaire.id,
            action__icontains="suppression",
            created_by=self.user
        )
        self.assertTrue(log.exists(), "Log de suppression manquant.")


    def test_non_owner_non_staff_cannot_update_partenaire(self):
        """
        ❌ Un utilisateur non staff et non propriétaire ne peut pas modifier
        """
        # Utilisateur 1 crée un partenaire
        partenaire = Partenaire.objects.create(**self.valid_data)
        partenaire.created_by = self.user
        partenaire.save()

        # Utilisateur 2, non staff, tente la modif
        autre_user = CustomUser.objects.create_user(
            email="nonstaff@example.com",
            username="other",
            password="OtherPass123",
            role="stagiaire",
            is_staff=False
        )
        refresh = RefreshToken.for_user(autre_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        url = reverse("partenaire-detail", args=[partenaire.id])
        response = self.client.patch(url, {"city": "Lyon"})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Accès réservé", response.data["detail"])

    def test_owner_can_update_partenaire(self):
        """
        ✅ Le propriétaire peut modifier son partenaire
        """
        partenaire = Partenaire.objects.create(**self.valid_data)
        partenaire.created_by = self.user
        partenaire.save()

        url = reverse("partenaire-detail", args=[partenaire.id])
        response = self.client.patch(url, {"city": "Lyon"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["localisation"]["ville"], "Lyon")
