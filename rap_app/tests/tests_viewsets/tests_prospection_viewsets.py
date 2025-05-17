# Tests corrigés pour correspondre aux ViewSets nettoyés et à la pagination enrichie

from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.contenttypes.models import ContentType
from datetime import timedelta
from django.utils import timezone

from ...models.centres import Centre
from ...models.custom_user import CustomUser
from ...models.formations import Formation
from ...models.partenaires import Partenaire
from ...models.prospection import Prospection, HistoriqueProspection, ProspectionChoices
from ...models.statut import Statut
from ...models.types_offre import TypeOffre
from ...models.logs import LogUtilisateur
from ...api.serializers.prospection_serializers import ProspectionSerializer


class ProspectionViewSetTestCase(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="admin@example.com",
            username="admin",
            password="adminpass",
            role="admin",
            is_staff=True
        )
        self.token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token.access_token}")

        self.centre = Centre.objects.create(nom="Centre X", code_postal="75000")
        self.statut = Statut.objects.create(nom="non_defini", couleur="#000000")
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

        self.partenaire = Partenaire.objects.create(nom="Partenaire Y", type="entreprise", created_by=self.user)

        self.valid_data = {
            "partenaire": self.partenaire.id,
            "formation": self.formation.id,
            "date_prospection": timezone.now().isoformat(),
            "type_contact": ProspectionChoices.TYPE_PREMIER_CONTACT,
            "motif": ProspectionChoices.MOTIF_PARTENARIAT,
            "statut": ProspectionChoices.STATUT_A_FAIRE,
            "objectif": ProspectionChoices.OBJECTIF_PRESENTATION,
            "commentaire": "Premier contact"
        }

        self.prospection = Prospection.objects.create(
            partenaire=self.partenaire,
            formation=self.formation,
            date_prospection=timezone.now(),
            type_contact=ProspectionChoices.TYPE_PREMIER_CONTACT,
            motif=ProspectionChoices.MOTIF_PARTENARIAT,
            statut=ProspectionChoices.STATUT_EN_COURS,
            objectif=ProspectionChoices.OBJECTIF_PRESENTATION,
            commentaire="Initial",
            created_by=self.user
        )

        self.list_url = reverse("prospection-list")

    def test_create_prospection(self):
        response = self.client.post(self.list_url, self.valid_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        obj_id = response.data.get("id") or response.data.get("data", {}).get("id")
        self.assertIsNotNone(obj_id)

        log = LogUtilisateur.objects.filter(
            content_type=ContentType.objects.get_for_model(Prospection),
            object_id=obj_id,
            action=LogUtilisateur.ACTION_CREATE,
            created_by=self.user
        )
        self.assertTrue(log.exists(), "Log de création manquant")

    def test_list_prospections(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        data = response.data.get("data", {}).get("results", [])
        self.assertIsInstance(data, list)

        ids = [p.get("id") for p in data if isinstance(p, dict)]
        self.assertIn(self.prospection.id, ids)

    def test_changer_statut(self):
        url = reverse("prospection-changer-statut", args=[self.prospection.id])
        payload = {"statut": ProspectionChoices.STATUT_A_RELANCER}
        response = self.client.post(url, data=payload, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertIn("data", response.data)
        self.assertEqual(response.data["data"].get("statut"), ProspectionChoices.STATUT_A_RELANCER)

    def test_prospection_historiques_action(self):
        url = reverse("prospection-historiques", args=[self.prospection.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("data", response.data)

    def test_delete_prospection_sets_annulee(self):
        prospection = Prospection.objects.create(
            partenaire=self.partenaire,
            formation=self.formation,
            date_prospection=timezone.now(),
            type_contact=ProspectionChoices.TYPE_PREMIER_CONTACT,
            motif=ProspectionChoices.MOTIF_PARTENARIAT,
            statut=ProspectionChoices.STATUT_EN_COURS,
            objectif=ProspectionChoices.OBJECTIF_PRESENTATION,
            commentaire="Suppression test",
            created_by=self.user
        )
        url = reverse("prospection-detail", args=[prospection.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        prospection.refresh_from_db()
        self.assertEqual(prospection.statut, ProspectionChoices.STATUT_ANNULEE)

    def test_serializer_accepts_null_formation(self):
        data = self.valid_data.copy()
        data["formation"] = None
        serializer = ProspectionSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_serializer_rejects_future_date(self):
        data = self.valid_data.copy()
        data["date_prospection"] = (timezone.now() + timedelta(days=1)).isoformat()
        serializer = ProspectionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("date_prospection", serializer.errors)

    def test_valid_update(self):
        serializer = ProspectionSerializer(
            instance=self.prospection,
            data={"commentaire": "Mise à jour"},
            partial=True
        )
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.commentaire, "Mise à jour")


class HistoriqueProspectionViewSetTestCase(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="admin@example.com",
            username="admin",
            password="adminpass",
            role="admin",
            is_staff=True
        )
        self.token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token.access_token}")

        centre = Centre.objects.create(nom="Centre Y", code_postal="75000")
        statut = Statut.objects.create(nom="non_defini", couleur="#000000")
        type_offre = TypeOffre.objects.create(nom="poec", couleur="#FF0000")

        formation = Formation.objects.create(
            nom="Formation A",
            centre=centre,
            statut=statut,
            type_offre=type_offre,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=5),
            created_by=self.user
        )

        partenaire = Partenaire.objects.create(nom="Entreprise ABC", type="entreprise", created_by=self.user)

        self.prospection = Prospection.objects.create(
            partenaire=partenaire,
            formation=formation,
            date_prospection=timezone.now(),
            type_contact=ProspectionChoices.TYPE_PREMIER_CONTACT,
            motif=ProspectionChoices.MOTIF_PARTENARIAT,
            statut=ProspectionChoices.STATUT_EN_COURS,
            objectif=ProspectionChoices.OBJECTIF_PRESENTATION,
            commentaire="Initial",
            created_by=self.user
        )

        self.historique = HistoriqueProspection.objects.create(
            prospection=self.prospection,
            ancien_statut=ProspectionChoices.STATUT_A_FAIRE,
            nouveau_statut=ProspectionChoices.STATUT_EN_COURS,
            type_contact=self.prospection.type_contact,
            commentaire="Premier contact",
            resultat="RDV fixé",
            prochain_contact=timezone.now().date() + timedelta(days=7),
            moyen_contact=ProspectionChoices.MOYEN_EMAIL,
            created_by=self.user
        )

        self.base_url = reverse("historiqueprospection-list")

    def test_list_historiques(self):
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get("data", {}).get("results", [])
        self.assertGreaterEqual(len(data), 1)

    def test_search_commentaire(self):
        url = self.base_url + "?search=Premier"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get("data", {}).get("results", [])
        self.assertGreaterEqual(len(data), 1)

    def test_retrieve_historique(self):
        url = reverse("historiqueprospection-detail", args=[self.historique.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["id"], self.historique.id)

    def test_ordering_by_date_modification(self):
        url = self.base_url + "?ordering=date_modification"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.data.get("data", {}).get("results", [])
        self.assertIsInstance(data, list)
        if len(data) >= 2:
            self.assertLessEqual(data[0]["date_modification"], data[1]["date_modification"])

    def test_filter_by_prospection_id(self):
        url = self.base_url + f"?prospection={self.prospection.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.data.get("data", {}).get("results", [])
        self.assertIsInstance(data, list)
        for h in data:
            self.assertEqual(h.get("prospection"), self.prospection.id)
