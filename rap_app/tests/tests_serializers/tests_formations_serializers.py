
# tests/test_formation_serializers.py

import tempfile
from datetime import date
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from rap_app.models.formations import Formation, HistoriqueFormation
from rap_app.models.centres import Centre
from rap_app.models.types_offre import TypeOffre
from rap_app.models.statut import Statut
from rap_app.models.partenaires import Partenaire
from rap_app.models.commentaires import Commentaire
from rap_app.models.documents import Document
from rap_app.models.evenements import Evenement

from rap_app.api.serializers.formations_serializers import (
    FormationSerializer,
    CommentaireSerializer,
    DocumentSerializer,
    EvenementSerializer,
    HistoriqueFormationSerializer,
)

User = get_user_model()


class FormationSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='commenter', email='commenter@example.com', password='pass')
        self.centre = Centre.objects.create(nom="Test Centre")
        self.type_offre = TypeOffre.objects.create(nom="crif")
        self.statut = Statut.objects.create(nom="formation_en_cours", couleur="#123456")

        self.formation = Formation.objects.create(
            nom="Test Formation",
            centre=self.centre,
            type_offre=self.type_offre,
            statut=self.statut,
            start_date=date(2025, 5, 1),
            end_date=date(2025, 6, 1),
            created_by=self.user
        )

    def test_serialization(self):
        serializer = FormationSerializer(instance=self.formation, context={"request": None})
        data = serializer.data
        self.assertIn("success", data)
        self.assertTrue(data["success"])
        self.assertIn("data", data)
        self.assertEqual(data["data"]["nom"], "Test Formation")

    def test_creation_invalid_date(self):
        payload = {
            "nom": "Invalid Formation",
            "centre_id": self.centre.pk,
            "type_offre_id": self.type_offre.pk,
            "statut_id": self.statut.pk,
            "start_date": "2025-06-01",
            "end_date": "2025-05-01",
        }
        serializer = FormationSerializer(data=payload, context={"request": self._fake_request()})
        self.assertFalse(serializer.is_valid())
        self.assertIn("start_date", serializer.errors)

    def _fake_request(self):
        class FakeRequest:
            user = self.user
        return FakeRequest()


class CommentaireSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='pass')
        self.formation = Formation.objects.create(nom="Formation", centre=Centre.objects.create(nom="X"), type_offre=TypeOffre.objects.create(nom="crif"), statut=Statut.objects.create(nom="formation_en_cours", couleur="#123456"), created_by=self.user)
        self.comment = Commentaire.objects.create(formation=self.formation, contenu="Test Comment", saturation=80, created_by=self.user)

    def test_comment_serializer(self):
        serializer = CommentaireSerializer(instance=self.comment)
        self.assertEqual(serializer.data["contenu"], "Test Comment")


class DocumentSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='pass')
        self.formation = Formation.objects.create(nom="Formation Doc", centre=Centre.objects.create(nom="X"), type_offre=TypeOffre.objects.create(nom="crif"), statut=Statut.objects.create(nom="formation_en_cours", couleur="#123456"), created_by=self.user)
        self.document = Document.objects.create(
            formation=self.formation,
            fichier=SimpleUploadedFile("test.pdf", b"dummy content"),
            nom_fichier="Test PDF",
            type_document="pdf",
            created_by=self.user
        )

    def test_document_serializer(self):
        serializer = DocumentSerializer(instance=self.document)
        self.assertEqual(serializer.data["nom_fichier"], "Test PDF")


class EvenementSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='pass')
        self.formation = Formation.objects.create(nom="Formation Event", centre=Centre.objects.create(nom="X"), type_offre=TypeOffre.objects.create(nom="crif"), statut=Statut.objects.create(nom="formation_en_cours", couleur="#123456"), created_by=self.user)
        self.evenement = Evenement.objects.create(
            formation=self.formation,
            type_evenement="forum",
            event_date=date.today(),
            created_by=self.user
        )

    def test_evenement_serializer(self):
        serializer = EvenementSerializer(instance=self.evenement)
        self.assertEqual(serializer.data["type_evenement"], "forum")


class HistoriqueFormationSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='pass')
        self.formation = Formation.objects.create(nom="Formation Hist", centre=Centre.objects.create(nom="X"), type_offre=TypeOffre.objects.create(nom="crif"), statut=Statut.objects.create(nom="formation_en_cours", couleur="#123456"), created_by=self.user)
        self.histo = HistoriqueFormation.objects.create(
            formation=self.formation,
            champ_modifie="nom",
            ancienne_valeur="Old",
            nouvelle_valeur="New",
            commentaire="Nom modifié",
            created_by=self.user
        )

    def test_historique_serializer(self):
        serializer = HistoriqueFormationSerializer(instance=self.histo)
        self.assertEqual(serializer.data["champ"], "nom")
        self.assertEqual(serializer.data["commentaire"], "Nom modifié")
