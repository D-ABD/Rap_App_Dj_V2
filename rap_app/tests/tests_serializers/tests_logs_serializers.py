from django.test import TestCase
from ...models.custom_user import CustomUser
from ...models.centres import Centre
from ...models.logs import LogUtilisateur
from ...api.serializers.logs_serializers import LogUtilisateurSerializer


class LogUtilisateurSerializerTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="log@test.com",
            username="loguser",
            password="testpass",
            role=CustomUser.ROLE_ADMIN,
            is_staff=True
        )
        self.centre = Centre.objects.create(nom="Centre Log Test", created_by=self.user)

        self.log = LogUtilisateur.log_action(
            instance=self.centre,
            action=LogUtilisateur.ACTION_UPDATE,
            user=self.user,
            details="Mise à jour testée"
        )

    def test_log_serializer_output(self):
        """
        ✅ Le serializer doit retourner les bons champs formatés
        """
        serializer = LogUtilisateurSerializer(instance=self.log)
        data = serializer.data

        self.assertEqual(data["id"], self.log.pk)
        self.assertEqual(data["action"], LogUtilisateur.ACTION_UPDATE)
        self.assertEqual(data["model"], "centre")  # ← Correction ici
        self.assertEqual(data["object_id"], self.centre.pk)
        self.assertEqual(data["user"], "loguser")
        self.assertIn("Mise à jour", data["details"])
        self.assertRegex(data["date"], r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}")

    def test_log_serializer_read_only_fields(self):
        """
        🚫 Le serializer ne doit pas permettre de modifier un log
        """
        serializer = LogUtilisateurSerializer(instance=self.log, data={"action": "suppression"}, partial=True)
        self.assertTrue(serializer.is_valid())
        # On ne teste pas .update car ce serializer est fait pour la lecture uniquement
        self.assertTrue(serializer.fields["action"].read_only)

    def test_log_date_format(self):
        """
        ✅ Vérifie le format YYYY-MM-DD HH:MM de la date
        """
        serializer = LogUtilisateurSerializer(instance=self.log)
        self.assertRegex(serializer.data["date"], r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}")

    def test_log_details_empty(self):
        """
        ✅ Vérifie que l'absence de détails ne cause pas d'erreur
        """
        log = LogUtilisateur.log_action(
            instance=self.centre,
            action=LogUtilisateur.ACTION_VIEW,
            user=self.user,
            details=""
        )
        serializer = LogUtilisateurSerializer(instance=log)
        self.assertEqual(serializer.data["details"], "")

    def test_log_system_action_user_none(self):
        """
        ✅ Test pour un log système sans utilisateur (user = "Système")
        """
        log = LogUtilisateur.log_system_action(
            action=LogUtilisateur.ACTION_EXPORT,
            user=None,
            details="Export global"
        )
        serializer = LogUtilisateurSerializer(instance=log)
        self.assertEqual(serializer.data["user"], "Système")

    def test_log_system_action_model_none(self):
        """
        ✅ Test pour un log système (content_object = LogUtilisateur lui-même)
        """
        log = LogUtilisateur.log_system_action(
            action=LogUtilisateur.ACTION_IMPORT,
            user=self.user,
            details="Import automatique"
        )
        serializer = LogUtilisateurSerializer(instance=log)
        self.assertEqual(serializer.data["model"], "logutilisateur")  # ← Correction ici
