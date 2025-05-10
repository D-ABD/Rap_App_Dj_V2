# tests/tests_models/tests_logs.py

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from ...models.custom_user import CustomUser

from ...models.logs import LogUtilisateur
from ...models.centres import Centre
from ...models.statut import Statut
from ...models.types_offre import TypeOffre
from ...models.formations import Formation

from .setup_base_tests import BaseModelTestSetupMixin


class LogUtilisateurModelTest(BaseModelTestSetupMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.centre = self.create_instance(Centre, nom="Centre Test")
        self.type_offre = self.create_instance(TypeOffre, nom=TypeOffre.CRIF)  # ✅ valeur valide
        self.statut = self.create_instance(Statut, nom=Statut.NON_DEFINI)
        self.formation = self.create_instance(
            Formation,
            nom="Formation Log",
            centre=self.centre,
            type_offre=self.type_offre,
            statut=self.statut,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),
            created_by=self.user
        )

    def test_log_creation_simple(self):
        log = LogUtilisateur.log_action(
            instance=self.formation,
            action=LogUtilisateur.ACTION_VIEW,
            user=self.user,
            details="Consultation de la fiche formation"
        )
        self.assertIsNotNone(log)
        self.assertEqual(log.content_object, self.formation)
        self.assertEqual(log.action, LogUtilisateur.ACTION_VIEW)
        self.assertEqual(log.created_by, self.user)

    def test_log_duplicate_blocked(self):
        log1 = LogUtilisateur.log_action(
            instance=self.formation,
            action=LogUtilisateur.ACTION_VIEW,
            user=self.user,
            details="Consultation de la fiche formation"
        )
        log2 = LogUtilisateur.log_action(
            instance=self.formation,
            action=LogUtilisateur.ACTION_VIEW,
            user=self.user,
            details="Consultation de la fiche formation"
        )
        self.assertIsNotNone(log1)
        self.assertIsNone(log2)  # doublon bloqué

    def test_log_sanitization(self):
        log = LogUtilisateur.log_action(
            instance=self.formation,
            action=LogUtilisateur.ACTION_UPDATE,
            user=self.user,
            details='{"password": "secret123", "note": "test"}'
        )
        self.assertIn('"*****"', log.details)
        self.assertNotIn("secret123", log.details)

    def test_log_system_action(self):
        system_user = CustomUser.objects.create_user(
            email="system@example.com",
            password="testpass",
            first_name="System",
            last_name="Bot"
        )
        log = LogUtilisateur.log_system_action(
            action=LogUtilisateur.ACTION_LOGIN,
            user=system_user,
            details="Connexion système réussie"
        )
        self.assertIsNotNone(log)
        self.assertEqual(log.action, LogUtilisateur.ACTION_LOGIN)
        self.assertEqual(log.created_by, system_user)
        self.assertIn("Connexion", log.details)

    def test_to_dict_output(self):
        log = LogUtilisateur.log_action(
            instance=self.formation,
            action=LogUtilisateur.ACTION_UPDATE,
            user=self.user,
            details="Mise à jour test"
        )
        data = log.to_dict()
        self.assertEqual(data["action"], LogUtilisateur.ACTION_UPDATE)
        self.assertEqual(data["model"], "formation")
        self.assertEqual(data["object_id"], self.formation.pk)
        self.assertEqual(data["user"], self.user.username)


# Tests supplémentaires à ajouter à votre classe LogUtilisateurModelTest

# Tests supplémentaires corrigés

# Tests supplémentaires avec corrections finales

    def test_log_with_multiple_sensitive_fields(self):
        """Teste la sanitization de plusieurs champs sensibles dans le même message."""
        details = '{"password": "secret123", "api_key": "ak_12345", "token": "t_67890", "note": "test"}'
        log = LogUtilisateur.log_action(
            instance=self.formation,
            action=LogUtilisateur.ACTION_UPDATE,
            user=self.user,
            details=details
        )
        # Vérifier que tous les champs sensibles sont masqués
        self.assertNotIn("secret123", log.details)
        self.assertNotIn("ak_12345", log.details)
        self.assertNotIn("t_67890", log.details)
        # Vérifier que le champ non sensible est conservé
        self.assertIn("test", log.details)


    def test_log_with_user_none(self):
        """Teste la création d'un log sans utilisateur (actions système)."""
        log = LogUtilisateur.log_action(
            instance=self.formation,
            action=LogUtilisateur.ACTION_VIEW,
            user=None,
            details="Vue automatique"
        )
        self.assertIsNotNone(log)
        self.assertIsNone(log.created_by)
        self.assertEqual(log.action, LogUtilisateur.ACTION_VIEW)

    def test_logs_ordering(self):
        """Teste l'ordre des logs (plus récents d'abord)."""
        import time
        # Nettoyer pour avoir un état propre
        LogUtilisateur.objects.all().delete()
        
        # Créer le premier log
        log1 = LogUtilisateur.log_action(
            instance=self.formation,
            action=LogUtilisateur.ACTION_CREATE,
            user=self.user,
            details="Premier log"
        )
        
        # Attendre un court instant pour assurer des timestamps différents
        time.sleep(0.1)
        
        # Créer le deuxième log avec une action différente
        log2 = LogUtilisateur.log_action(
            instance=self.formation,
            action=LogUtilisateur.ACTION_EXPORT,
            user=self.user,
            details="Deuxième log"
        )
        
        # ⚠️ Correction: Ne pas utiliser content_object dans le filtre
        # Utiliser content_type et object_id à la place
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(self.formation)
        
        logs = list(LogUtilisateur.objects.filter(
            content_type=content_type,
            object_id=self.formation.pk
        ).order_by('-created_at')[:2])
        
        # Vérifier que le plus récent est en premier
        self.assertEqual(logs[0].id, log2.id, "Le log le plus récent devrait être en premier")
        self.assertEqual(logs[1].id, log1.id, "Le log le plus ancien devrait être en second")

    def test_log_with_invalid_input(self):
        """Teste la robustesse face à des entrées invalides."""
        # Test avec une instance None
        log_none = LogUtilisateur.log_action(
            instance=None,
            action=LogUtilisateur.ACTION_VIEW,
            user=self.user
        )
        self.assertIsNone(log_none)
        
        # Test avec une action vide
        log_empty = LogUtilisateur.log_action(
            instance=self.formation,
            action="",
            user=self.user
        )
        # Selon votre implémentation, peut être None ou un log valide
        # Pas d'assertion, juste vérifier qu'il n'y a pas d'exception

    def test_log_different_content_types(self):
        """Teste la création de logs pour différents modèles."""
        from django.contrib.contenttypes.models import ContentType
        
        # Nettoyer les logs existants
        LogUtilisateur.objects.all().delete()
        
        # Log pour un Centre
        log_centre = LogUtilisateur.log_action(
            instance=self.centre,
            action=LogUtilisateur.ACTION_VIEW,
            user=self.user,
            details="Vue du centre"
        )
        self.assertIsNotNone(log_centre)
        self.assertEqual(log_centre.content_object, self.centre)
        
        # Log pour un Statut
        log_statut = LogUtilisateur.log_action(
            instance=self.statut,
            action=LogUtilisateur.ACTION_VIEW,
            user=self.user,
            details="Vue du statut"
        )
        self.assertIsNotNone(log_statut)
        self.assertEqual(log_statut.content_object, self.statut)
        
        # Vérifier qu'on peut retrouver les logs par type de contenu
        centre_ct = ContentType.objects.get_for_model(self.centre)
        centre_logs = LogUtilisateur.objects.filter(content_type=centre_ct)
        self.assertEqual(centre_logs.count(), 1, 
                        f"Attendu 1 log pour le Centre, trouvé {centre_logs.count()}")
        self.assertEqual(centre_logs[0].id, log_centre.id)


    def test_log_with_different_sensitive_formats(self):
        """Teste la sanitization de différents formats de données sensibles."""
        # Test format par format pour identifier lesquels fonctionnent réellement
        
        # Test 1: Format double quotes (devrait fonctionner)
        log1 = LogUtilisateur.log_action(
            instance=self.formation,
            action=LogUtilisateur.ACTION_UPDATE,
            user=self.user,
            details='{"password": "secret123", "note": "test"}'
        )
        self.assertIsNotNone(log1)
        self.assertNotIn("secret123", log1.details)
        self.assertIn("*****", log1.details)
        
        # Test 2: Format JSON sans quotes (devrait fonctionner)
        log2 = LogUtilisateur.log_action(
            instance=self.formation,
            action=LogUtilisateur.ACTION_CREATE,  # Action différente
            user=self.user,
            details='password:secret123'
        )
        self.assertIsNotNone(log2)
        self.assertNotIn("secret123", log2.details)
        self.assertIn("*****", log2.details)