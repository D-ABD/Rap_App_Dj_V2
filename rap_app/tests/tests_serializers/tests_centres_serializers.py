from django.test import TestCase
from rap_app.models.centres import Centre
from ...api.serializers.centres_serializers import CentreSerializer

class CentreSerializerTestCase(TestCase):
    def setUp(self):
        self.centre = Centre.objects.create(nom="Centre Test", code_postal="75001")

    def test_serializer_output(self):
        serializer = CentreSerializer(instance=self.centre)
        data = serializer.data
        self.assertEqual(data["nom"], "Centre Test")
        self.assertEqual(data["code_postal"], "75001")
        self.assertIn("full_address", data)
