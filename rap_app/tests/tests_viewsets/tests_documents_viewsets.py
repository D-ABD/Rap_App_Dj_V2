from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from ...models.documents import Document
from ...models.formations import Formation
from ...models.centres import Centre
from ...models.types_offre import TypeOffre
from ...models.statut import Statut
from ...models.custom_user import CustomUser


class DocumentViewSetTestCase(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="userdoc",
            email="userdoc@example.com",
            password="pass",
            is_staff=True,  # ✅ Nécessaire pour les permissions
            role=CustomUser.ROLE_ADMIN  # ✅ Si tu gères les rôles
        )
        self.client.force_authenticate(user=self.user)

        self.centre = Centre.objects.create(nom="TestCentre", created_by=self.user)
        self.type_offre = TypeOffre.objects.create(nom="crif", created_by=self.user)
        self.statut = Statut.objects.create(nom="non_defini", couleur="#000000", created_by=self.user)

        self.formation = Formation.objects.create(
            nom="FormationDoc",
            centre=self.centre,
            type_offre=self.type_offre,
            statut=self.statut,
            created_by=self.user
        )

        self.file = SimpleUploadedFile("doc_test.pdf", b"file_content", content_type="application/pdf")
        self.document = Document.objects.create(
            formation=self.formation,
            nom_fichier="doc_test.pdf",
            fichier=self.file,
            type_document=Document.PDF,
            created_by=self.user
        )

    def test_list_documents(self):
        url = reverse("document-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("data", response.data)

    def test_retrieve_document(self):
        url = reverse("document-detail", args=[self.document.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("data", {}).get("id"), self.document.id)

    def test_create_document(self):
        url = reverse("document-list")
        file = SimpleUploadedFile("new_doc.pdf", b"%PDF-1.4...", content_type="application/pdf")
        data = {
            "formation": self.formation.id,
            "nom_fichier": "new_doc.pdf",
            "type_document": Document.PDF,
            "fichier": file,
        }
        response = self.client.post(url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Document.objects.filter(nom_fichier="new_doc.pdf").exists())

    def test_update_document(self):
        url = reverse("document-detail", args=[self.document.id])
        data = {"nom_fichier": "updated_name.pdf"}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("data", {}).get("nom_fichier"), "updated_name.pdf")

    def test_delete_document(self):
        url = reverse("document-detail", args=[self.document.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Document.objects.filter(id=self.document.id).exists())

    def test_documents_by_formation(self):
        url = reverse("document-par-formation")
        response = self.client.get(url, {"formation": self.formation.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data.get("data", [])), 1)

    def test_export_csv(self):
        url = reverse("document-export-csv")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/csv")
