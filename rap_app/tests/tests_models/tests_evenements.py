
from django.core.exceptions import ValidationError
from django.utils import timezone
from ...models import Evenement, Formation, Centre, TypeOffre, Statut
from .setup_base_tests import BaseModelTestSetupMixin

class EvenementModelTest(BaseModelTestSetupMixin):
    """🧪 Tests unitaires du modèle Evenement."""

    def setUp(self):
        super().setUp()
        self.centre = self.create_instance(Centre, nom="Centre Test")
        self.type_offre = self.create_instance(TypeOffre, nom=TypeOffre.CRIF)
        self.statut = self.create_instance(Statut, nom=Statut.NON_DEFINI)
        self.formation = self.create_instance(
            Formation,
            nom="Formation Test",
            centre=self.centre,
            type_offre=self.type_offre,
            statut=self.statut
        )

    def test_create_valid_evenement(self):
        evt = Evenement(
            formation=self.formation,
            type_evenement=Evenement.TypeEvenement.JOB_DATING,
            event_date=timezone.now().date(),
            participants_prevus=10,
            participants_reels=8,
            created_by=self.user,
            updated_by=self.user
        )
        evt.full_clean()
        evt.save()
        self.assertEqual(evt.get_temporal_status(), Evenement.StatutTemporel.AUJOURD_HUI)
        self.assertEqual(evt.get_participation_rate(), 80.0)

    def test_description_autre_required_if_type_autre(self):
        evt = Evenement(
            type_evenement=Evenement.TypeEvenement.AUTRE,
            event_date=timezone.now().date()
        )
        with self.assertRaises(ValidationError):
            evt.full_clean()

    def test_participation_rate_none_when_missing_data(self):
        evt = Evenement(
            type_evenement=Evenement.TypeEvenement.FORUM,
            participants_prevus=None,
            participants_reels=5
        )
        self.assertIsNone(evt.get_participation_rate())

    def test_str_representation_contains_label_and_date(self):
        evt = self.create_instance(
            Evenement,
            formation=self.formation,
            type_evenement=Evenement.TypeEvenement.FORUM,
            event_date=timezone.now().date()
        )
        self.assertIn("Forum", str(evt))
        self.assertIn(str(evt.event_date.year), str(evt))

    def test_to_serializable_dict_keys(self):
        evt = self.create_instance(
            Evenement,
            formation=self.formation,
            type_evenement=Evenement.TypeEvenement.FORUM,
            event_date=timezone.now().date()
        )
        data = evt.to_serializable_dict()
        expected_keys = [
            "id", "formation_id", "type_evenement", "type_evenement_display",
            "event_date", "event_date_formatted", "participants_prevus", "participants_reels",
            "taux_participation", "status", "status_label", "status_color"
        ]
        for key in expected_keys:
            self.assertIn(key, data)

    def test_taux_participation_format(self):
        evt = self.create_instance(
            Evenement,
            formation=self.formation,
            type_evenement=Evenement.TypeEvenement.FORUM,
            event_date=timezone.now().date(),
            participants_prevus=10,
            participants_reels=9
        )
        self.assertEqual(evt.taux_participation_formatted, "90.0%")
        evt.participants_reels = None
        self.assertEqual(evt.taux_participation_formatted, "N/A")

    def test_clean_warns_on_old_event_date(self):
        old_date = timezone.now().date() - timezone.timedelta(days=400)
        evt = Evenement(
            formation=self.formation,
            type_evenement=Evenement.TypeEvenement.FORUM,
            event_date=old_date,
            created_by=self.user
        )
        with self.assertLogs("application.evenements", level="WARNING") as cm:
            evt.full_clean()
            self.assertIn("Date ancienne", cm.output[0])

    def test_temporal_status_past_today_soon_future(self):
        today = timezone.now().date()
        cases = {
            Evenement.StatutTemporel.PASSE: today - timezone.timedelta(days=1),
            Evenement.StatutTemporel.AUJOURD_HUI: today,
            Evenement.StatutTemporel.BIENTOT: today + timezone.timedelta(days=3),
            Evenement.StatutTemporel.FUTUR: today + timezone.timedelta(days=30),
        }
        for expected_status, date in cases.items():
            evt = self.create_instance(
                Evenement,
                formation=self.formation,
                type_evenement=Evenement.TypeEvenement.JOB_DATING,
                event_date=date
            )
            self.assertEqual(evt.get_temporal_status(), expected_status)

    def test_participation_status_levels(self):
        evt_high = self.create_instance(Evenement, formation=self.formation, type_evenement=Evenement.TypeEvenement.FORUM, participants_prevus=10, participants_reels=10)
        self.assertEqual(evt_high.participation_status, 'success')
        evt_mid = self.create_instance(Evenement, formation=self.formation, type_evenement=Evenement.TypeEvenement.FORUM, participants_prevus=10, participants_reels=7)
        self.assertEqual(evt_mid.participation_status, 'warning')
        evt_low = self.create_instance(Evenement, formation=self.formation, type_evenement=Evenement.TypeEvenement.FORUM, participants_prevus=10, participants_reels=3)
        self.assertEqual(evt_low.participation_status, 'danger')
