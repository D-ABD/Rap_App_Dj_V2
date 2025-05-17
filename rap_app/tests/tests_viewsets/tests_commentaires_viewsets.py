from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from ...models.commentaires import Commentaire
from ...models.formations import Formation
from ...models.custom_user import CustomUser
from ...models.centres import Centre
from ...models.statut import Statut
from ...models.types_offre import TypeOffre


class CommentaireViewSetTestCase(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="admin@example.com",
            username="admin",
            password="pass",
            is_staff=True,
            role=CustomUser.ROLE_ADMIN,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.centre = Centre.objects.create(nom="Centre Test", code_postal="75001")
        self.statut = Statut.objects.create(nom="non_defini", couleur="#00FF00")
        self.type_offre = TypeOffre.objects.create(nom="poec", couleur="#FF0000")

        self.formation = Formation.objects.create(
            nom="Formation Test",
            centre=self.centre,
            statut=self.statut,
            type_offre=self.type_offre,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=5),
            created_by=self.user
        )

        self.commentaire = Commentaire.objects.create(
            formation=self.formation,
            contenu="Contenu de test",
            saturation=85,
            created_by=self.user
        )

    def get_data(self, response):
        return response.data.get("data", response.data)

    def test_list_commentaires(self):
        url = reverse("commentaire-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("data", response.data)

    def test_detail_commentaire(self):
        url = reverse("commentaire-detail", args=[self.commentaire.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.get_data(response)["id"], self.commentaire.id)

    def test_create_commentaire_valide(self):
        url = reverse("commentaire-list")
        payload = {
            "formation": self.formation.id,
            "contenu": "Nouveau commentaire",
            "saturation": 70
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("data", response.data)
        self.assertEqual(self.get_data(response)["saturation"], 70)

    def test_create_commentaire_invalide_contenu(self):
        url = reverse("commentaire-list")
        payload = {
            "formation": self.formation.id,
            "contenu": "   ",
            "saturation": 50
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("contenu", response.data)

    def test_create_commentaire_invalide_saturation(self):
        url = reverse("commentaire-list")
        payload = {
            "formation": self.formation.id,
            "contenu": "Contenu correct",
            "saturation": 150
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("saturation", response.data)

    def test_update_commentaire(self):
        url = reverse("commentaire-detail", args=[self.commentaire.id])
        payload = {
            "formation": self.formation.id,
            "contenu": "Contenu modifié",
            "saturation": 60
        }
        response = self.client.put(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.get_data(response)["contenu"], "Contenu modifié")

    def test_delete_commentaire(self):
        url = reverse("commentaire-detail", args=[self.commentaire.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Commentaire.objects.filter(pk=self.commentaire.id).exists())

    def test_filtrage_par_formation(self):
        url = reverse("commentaire-list") + f"?formation_id={self.formation.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self.get_data(response)["results"]
        for c in results:
            commentaire = c["data"] if "data" in c else c
            self.assertEqual(commentaire["formation_id"], self.formation.id)


    def test_filtrage_par_recherche(self):
        url = reverse("commentaire-list") + "?search=test"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self.get_data(response)["results"]
        self.assertTrue(any("test" in c["contenu"].lower() for c in results))

    def test_endpoint_saturation_stats(self):
        url = reverse("commentaire-saturation-stats")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        stats = self.get_data(response)
        self.assertIn("avg", stats)
        self.assertEqual(stats["count"], 1)
