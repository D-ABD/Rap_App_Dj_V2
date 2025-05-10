from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from django.core.cache import cache

from ...models.models_test import DummyModel


User = get_user_model()


class BaseModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="securepassword123"
        )

    def test_create_sets_created_fields(self):
        obj = DummyModel(name="Test Entry")
        obj.save(user=self.user)

        self.assertIsNotNone(obj.pk)
        self.assertEqual(obj.created_by, self.user)
        self.assertEqual(obj.updated_by, self.user)
        self.assertTrue(obj.is_active)
        self.assertIsNotNone(obj.created_at)
        self.assertIsNotNone(obj.updated_at)

    def test_update_sets_updated_by_only(self):
        creator = User.objects.create_user(
            username="creator",
            email="creator@example.com",
            password="pass"
        )
        editor = User.objects.create_user(
            username="editor",
            email="editor@example.com",
            password="pass"
        )
        obj = DummyModel.objects.create(name="Initial", created_by=creator, updated_by=creator)

        obj.name = "Updated"
        obj.save(user=editor)

        self.assertEqual(obj.updated_by, editor)
        self.assertEqual(obj.created_by, creator)

    def test_get_changed_fields(self):
        obj = DummyModel.objects.create(name="Original")
        obj.name = "Modified"
        changes = obj.get_changed_fields()

        self.assertIn("name", changes)
        self.assertEqual(changes["name"], ("Original", "Modified"))

    def test_str_and_repr(self):
        obj = DummyModel.objects.create(name="Label")
        self.assertEqual(str(obj), f"DummyModel #{obj.pk}")
        self.assertEqual(repr(obj), f"<DummyModel(id={obj.pk})>")

    def test_to_serializable_dict(self):
        obj = DummyModel.objects.create(name="Serializable", created_by=self.user, updated_by=self.user)
        data = obj.to_serializable_dict()
        self.assertEqual(data["name"], "Serializable")
        self.assertEqual(data["created_by"]["id"], self.user.id)

    def test_get_by_id_and_filtered_queryset(self):
        obj = DummyModel.objects.create(name="Filtered")
        found = DummyModel.get_by_id(obj.pk)
        self.assertEqual(found, obj)

        queryset = DummyModel.get_filtered_queryset(name="Filtered")
        self.assertTrue(queryset.exists())

    def test_cache_invalidation_on_save_and_delete(self):
        obj = DummyModel.objects.create(name="CacheTest")
        cache.set(f"DummyModel_{obj.pk}", "cached_value")
        cache.set(f"DummyModel_list", "cached_list")

        obj.name = "Updated"
        obj.save(user=self.user)

        self.assertIsNone(cache.get(f"DummyModel_{obj.pk}"))
        self.assertIsNone(cache.get(f"DummyModel_list"))

        obj.delete()
        self.assertFalse(DummyModel.objects.filter(pk=obj.pk).exists())

    def test_get_by_id_invalid_raises_value_error(self):
        with self.assertRaises(ValueError):
            DummyModel.get_by_id("invalid")
