from django.core.exceptions import ValidationError
from django.utils.timezone import now

from ...models import Centre
from .setup_base_tests import BaseModelTestSetupMixin

class CentreModelTest(BaseModelTestSetupMixin):
    """🧪 Tests complets du modèle Centre."""

    def test_str_and_repr(self):
        centre = self.create_instance(Centre, nom="Centre A", code_postal="75000")
        self.assertEqual(str(centre), "Centre A")
        self.assertIn("Centre", repr(centre))



    def test_full_address(self):
        centre = self.create_instance(Centre, nom="Centre Test", code_postal="75001")
        self.assertEqual(centre.full_address(), "Centre Test (75001)")

    def test_validation_code_postal(self):
        with self.assertRaises(ValidationError):
            centre = Centre(nom="Centre Invalide", code_postal="75ABC")
            centre.full_clean()
        with self.assertRaises(ValidationError):
            centre = Centre(nom="Centre Invalide", code_postal="7500")
            centre.full_clean()

    def test_cache_invalidation(self):
        centre = self.create_instance(Centre, nom="Centre Cache", code_postal="75000")

        # Crée une instance liée dans la BDD
        from ...models.prepacomp import PrepaCompGlobal
        PrepaCompGlobal.objects.create(centre=centre, annee=now().year)

        # Recharge le centre depuis la base pour éviter les incohérences
        centre = Centre.objects.get(pk=centre.pk)

        # Déclenche le cache
        value = centre.nb_prepa_comp_global
        self.assertEqual(value, 1)

        # ✅ Vérifie que la propriété est bien mise en cache sous le bon nom
        self.assertIn('nb_prepa_comp_global', centre.__dict__)

        # Invalide le cache
        centre.invalidate_caches()

        # ✅ Vérifie que le cache est supprimé
        self.assertNotIn('nb_prepa_comp_global', centre.__dict__)


    def test_to_serializable_dict(self):
        centre = self.create_instance(Centre, nom="Centre JSON", code_postal="12345")
        data = centre.to_serializable_dict()
        self.assertIn("nom", data)
        self.assertIn("code_postal", data)
        self.assertEqual(data["nom"], "Centre JSON")

    def test_get_csv_row_and_headers(self):
        centre = self.create_instance(Centre, nom="Centre CSV", code_postal="75010")
        row = centre.to_csv_row()
        self.assertEqual(row[1], "Centre CSV")
        self.assertEqual(row[2], "75010")
        self.assertEqual(Centre.get_csv_headers()[1], "Nom du centre")

    def test_managers_by_code_postal(self):
        self.create_instance(Centre, nom="Centre A", code_postal="75000")
        self.create_instance(Centre, nom="Centre B", code_postal="75000")
        centres = Centre.custom.by_code_postal("75000")
        self.assertEqual(centres.count(), 2)

    def test_mark_as_inactive_returns_false(self):
        centre = self.create_instance(Centre, nom="Centre Inactif", code_postal="75000")
        self.assertFalse(centre.mark_as_inactive())

    def test_handle_related_update_does_not_crash(self):
        centre = self.create_instance(Centre, nom="Centre Rel", code_postal="75000")
        try:
            centre.handle_related_update("Objet fictif")
        except Exception as e:
            self.fail(f"handle_related_update a levé une exception: {e}")

    def test_get_centres_with_stats(self):
        self.create_instance(Centre, nom="Centre Stat", code_postal="75000")
        queryset = Centre.get_centres_with_stats()
        self.assertGreaterEqual(queryset.count(), 1)

    def test_search_manager(self):
        self.create_instance(Centre, nom="Centre Alpha", code_postal="12345")
        self.create_instance(Centre, nom="Centre Beta", code_postal="54321")
        results = Centre.custom.search("Alpha")
        self.assertEqual(results.count(), 1)

    def test_with_prepa_counts(self):
        self.create_instance(Centre, nom="Centre Compte", code_postal="99999")
        queryset = Centre.custom.with_prepa_counts()
        self.assertGreaterEqual(queryset.count(), 1)


    def test_prepa_global_returns_none(self):
        centre = self.create_instance(Centre, nom="Centre Test", code_postal="75000")
        self.assertIsNone(centre.prepa_global())

    def test_delete_centre(self):
        centre = self.create_instance(Centre, nom="Centre Suppr", code_postal="75000")
        pk = centre.pk
        centre.delete()
        self.assertFalse(Centre.objects.filter(pk=pk).exists())
