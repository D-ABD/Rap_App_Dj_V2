import pytest
from django.utils import timezone
from rap_app_project.rap_app.models.centres import Centre
from rap_app_project.rap_app.api.serializers.centres_serializers import CentreSerializer

@pytest.mark.django_db
def test_centre_serializer_valid_data():
    data = {
        "nom": "Centre Test",
        "code_postal": "75001",
        "objectif_annuel_prepa": 100,
        "objectif_hebdomadaire_prepa": 10,
        "objectif_annuel_jury": 50,
        "objectif_mensuel_jury": 5
    }
    serializer = CentreSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    centre = serializer.save()
    assert centre.nom == "Centre Test"
    assert centre.code_postal == "75001"

@pytest.mark.django_db
def test_centre_serializer_invalid_postal_code():
    data = {
        "nom": "Centre Invalide",
        "code_postal": "7500",  # Code postal invalide (4 chiffres)
        "objectif_annuel_prepa": 100,
        "objectif_hebdomadaire_prepa": 10,
        "objectif_annuel_jury": 50,
        "objectif_mensuel_jury": 5
    }
    serializer = CentreSerializer(data=data)
    assert not serializer.is_valid()
    assert "code_postal" in serializer.errors
