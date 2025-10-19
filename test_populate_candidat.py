from rap_app.models import Candidat, CerfaContrat

candidat = Candidat.objects.first()
if not candidat:
    ("❌ Aucun candidat trouvé.")
else:
    (f"✅ Test du candidat : {candidat.nom_complet}")
    cerfa = CerfaContrat(candidat=candidat)
    cerfa.populate_from_candidat(candidat)

    # --- Vérification bloc Apprenti ---
    correspondances_apprenti = {
        "apprenti_nom_naissance": "nom_naissance",
        "apprenti_prenom": "prenom",
        "apprenti_date_naissance": "date_naissance",
        "apprenti_sexe": "sexe",
        "apprenti_email": "email",
        "apprenti_telephone": "telephone",
        "apprenti_numero": "street_number",
        "apprenti_voie": "street_name",
        "apprenti_complement": "street_complement",
        "apprenti_code_postal": "code_postal",
        "apprenti_commune": "ville",
        "apprenti_departement_naissance": "departement_naissance",
        "apprenti_commune_naissance": "commune_naissance",
        "apprenti_nationalite": "nationalite",
    }

    ("\n📋 Vérification du bloc APPRENTI :\n")
    for cerfa_field, candidat_field in correspondances_apprenti.items():
        cerfa_val = getattr(cerfa, cerfa_field)
        candidat_val = getattr(candidat, candidat_field)
        ok = cerfa_val == candidat_val
        status = "✅" if ok else "⚠️"
        (f"{status} {cerfa_field:<30} ← {candidat_field:<25} | CERFA={cerfa_val!r} / CANDIDAT={candidat_val!r}")

    # --- Vérification bloc Représentant légal ---
    correspondances_repr = {
        "representant_nom": "representant_nom_naissance",
        "representant_lien": "representant_lien",
        "representant_adresse_voie": "representant_street_name",
        "representant_code_postal": "representant_zip_code",
        "representant_commune": "representant_city",
        "representant_email": "representant_email",
    }

    ("\n📋 Vérification du bloc REPRÉSENTANT LÉGAL :\n")
    for cerfa_field, candidat_field in correspondances_repr.items():
        cerfa_val = getattr(cerfa, cerfa_field)
        candidat_val = getattr(candidat, candidat_field)
        ok = cerfa_val == candidat_val
        status = "✅" if ok else "⚠️"
        (f"{status} {cerfa_field:<30} ← {candidat_field:<30} | CERFA={cerfa_val!r} / CANDIDAT={candidat_val!r}")

    ("\n🎯 Test terminé — vérifie les lignes ⚠️ pour ajuster si besoin.")
 