from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.core.files.uploadedfile import SimpleUploadedFile

from ...models.custom_user import CustomUser
from ...models.centres import Centre
from ...models.statut import Statut
from ...models.types_offre import TypeOffre
from ...models.formations import Formation
from ...models.documents import Document
from ...api.serializers.documents_serializers import DocumentSerializer


class DocumentSerializerTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass",
            is_staff=True
        )
        self.centre = Centre.objects.create(nom="Test Centre", code_postal="75000", created_by=self.user)
        self.statut = Statut.objects.create(nom="non_defini", couleur="#000000", created_by=self.user)
        self.type_offre = TypeOffre.objects.create(nom="poec", couleur="#FF0000", created_by=self.user)
        self.formation = Formation.objects.create(
            nom="Test Formation",
            centre=self.centre,
            statut=self.statut,
            type_offre=self.type_offre,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=10),
            created_by=self.user
        )

    def _mock_request(self):
        class MockRequest:
            user = self.user
        return MockRequest()

    def test_serializer_valid(self):
        file = SimpleUploadedFile("test.pdf", b"%PDF-1.4...", content_type="application/pdf")
        data = {
            "formation": self.formation.id,
            "nom_fichier": "test.pdf",
            "type_document": Document.PDF,
            "fichier": file,
        }
        serializer = DocumentSerializer(data=data, context={"request": self._mock_request()})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_serializer_missing_formation(self):
        file = SimpleUploadedFile("test.pdf", b"%PDF-1.4...", content_type="application/pdf")
        data = {
            "nom_fichier": "test.pdf",
            "type_document": Document.PDF,
            "fichier": file,
        }
        serializer = DocumentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("formation", serializer.errors)

    def test_invalid_extension(self):
        file = SimpleUploadedFile("malware.exe", b"binarydata", content_type="application/octet-stream")
        data = {
            "formation": self.formation.id,
            "nom_fichier": "malware.exe",
            "type_document": Document.PDF,
            "fichier": file,
        }
        serializer = DocumentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("fichier", serializer.errors)

    def test_to_representation_structure(self):
        file = SimpleUploadedFile("test.pdf", b"%PDF-1.4...", content_type="application/pdf")
        doc = Document.objects.create(
            formation=self.formation,
            nom_fichier="test.pdf",
            fichier=file,
            type_document=Document.PDF,
            created_by=self.user
        )
        serializer = DocumentSerializer(instance=doc)
        data = serializer.data
        self.assertIn("success", data)
        self.assertTrue(data["success"])
        self.assertIn("data", data)
        self.assertEqual(data["data"]["nom_fichier"], "test.pdf")
