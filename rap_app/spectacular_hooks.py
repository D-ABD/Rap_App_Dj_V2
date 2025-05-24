from drf_spectacular.plumbing import build_basic_type
from drf_spectacular.types import OpenApiTypes

def preprocess_hook(endpoints):
    return endpoints

def postprocess_hook(result, generator, request, public):
    # Correction manuelle des noms d'enum
    enum_mappings = {
        'rap_app.Prospection.statut': 'StatutEnum',
        'rap_app.Prospection.objectif': 'ObjectifEnum',
        'rap_app.Prospection.motif': 'MotifEnum',
        'rap_app.Prospection.type_contact': 'TypeContactEnum',
        'rap_app.HistoriqueProspection.ancien_statut': 'AncienStatutEnum',
        'rap_app.HistoriqueProspection.nouveau_statut': 'NouveauStatutEnum',
    }

    schemas = result.get('components', {}).get('schemas', {})

    for schema_name, schema in schemas.items():
        if 'properties' in schema:
            for prop_name, prop in schema['properties'].items():
                if 'enum' in prop:
                    key = f"rap_app.{schema_name}.{prop_name}"
                    if key in enum_mappings:
                        prop['x-enum-name'] = enum_mappings[key]

    return result
