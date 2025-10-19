"""
cerfa_field_mapper.py
─────────────────────
Outil utilitaire pour :
  ✅ Explorer les champs du PDF CERFA (via pdfrw)
  ✅ Générer automatiquement un mapping CERFA_FIELD_MAP
     entre les champs PDF et le modèle Django CerfaContrat

Utilisation :
  python rap_app/utils/cerfa_field_mapper.py --scan
      → Affiche la liste brute des champs PDF (exploration)

  python rap_app/utils/cerfa_field_mapper.py --dry-run
      → Génère un mapping automatique sans rien écrire

  python rap_app/utils/cerfa_field_mapper.py
      → Génère et sauvegarde constants_cerfa.py
"""

import os
import re
import sys
import django
from difflib import SequenceMatcher
from pdfrw import PdfReader
from django.conf import settings
from django.apps import apps

# ============================================================
# ⚙️ Initialisation Django
# ============================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))
sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rap_app_project.settings")
django.setup()

# ============================================================
# 🔧 Fonctions utilitaires
# ============================================================
def normalize_field_name(name: str) -> str:
    """Nettoie et normalise le nom de champ PDF."""
    if not name:
        return ""
    replacements = {
        "#C3#A0": "à", "#C3#A9": "é", "#C3#A8": "è", "#C3#A7": "ç",
        "#C3#AA": "ê", "#C3#AB": "ë", "#C3#B4": "ô", "#C3#BB": "û", "#C3#B9": "ù",
    }
    for k, v in replacements.items():
        name = name.replace(k, v)
    return re.sub(r"[^a-zA-Z0-9_àéèùçÀÉÈÇÔÛÙ ]", "", name).strip()

def similarity(a: str, b: str) -> float:
    """Renvoie un score de similarité entre 0 et 1 entre deux chaînes."""
    a, b = a.lower().replace("_", " "), b.lower().replace("_", " ")
    return SequenceMatcher(None, a, b).ratio()

# ============================================================
# 📄 Extraction des champs PDF
# ============================================================
def extract_pdf_fields() -> list[str]:
    """Liste tous les champs interactifs du PDF CERFA."""
    template_path = os.path.join(settings.BASE_DIR, "rap_app/static/cerfa/cerfa_10103-14.pdf")

    if not os.path.exists(template_path):
        (f"❌ Fichier introuvable : {template_path}")
        return []

    (f"✅ Fichier trouvé : {template_path}\n")
    pdf = PdfReader(template_path)
    fields = set()

    for page_number, page in enumerate(pdf.pages, start=1):
        annotations = getattr(page, "Annots", [])
        for annot in annotations:
            key = getattr(annot.T, "to_unicode", lambda: None)()
            if key:
                fields.add(normalize_field_name(key))

    (f"✅ {len(fields)} champs détectés dans le PDF (nettoyés)\n")
    return sorted(fields)

# ============================================================
# 🧩 Extraction des champs du modèle Django
# ============================================================
def extract_model_fields() -> list[str]:
    """Retourne la liste des champs du modèle CerfaContrat."""
    try:
        CerfaContrat = apps.get_model("rap_app", "cerfacontrat")
    except LookupError:
        ("❌ Modèle CerfaContrat introuvable.")
        return []
    model_fields = [f.name for f in CerfaContrat._meta.get_fields()]
    (f"✅ {len(model_fields)} champs trouvés dans le modèle CerfaContrat\n")
    return model_fields

# ============================================================
# 🧠 Génération automatique du mapping
# ============================================================
def generate_field_map(dry_run=False):
    """Associe les champs PDF aux champs Django par similarité."""
    pdf_fields = extract_pdf_fields()
    model_fields = extract_model_fields()

    if not pdf_fields or not model_fields:
        ("⚠️ Impossible de générer le mapping : champs manquants.")
        return

    cerfa_field_map = {}
    for pdf_field in pdf_fields:
        best_match, best_score = None, 0.0
        for model_field in model_fields:
            score = similarity(pdf_field, model_field)
            if score > best_score:
                best_match, best_score = model_field, score
        cerfa_field_map[pdf_field] = best_match if best_score > 0.35 else ""

    # Chemin de sortie
    output_path = os.path.join(settings.BASE_DIR, "rap_app/utils/constants_cerfa.py")

    if dry_run:
        ("\n🔍 Mode DRY-RUN : aperçu du mapping (aucun fichier modifié)\n")
        ("CERFA_FIELD_MAP = {")
        for k, v in sorted(cerfa_field_map.items()):
            (f'    "{k}": "{v}",')
        ("}")
        ("\n💡 Lance sans --dry-run pour sauvegarder dans constants_cerfa.py")
        return

    # Écriture du mapping dans un fichier Python
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# ⚙️ Généré automatiquement par cerfa_field_mapper.py\n")
        f.write("# Vérifie manuellement les correspondances avant usage.\n\n")
        f.write("CERFA_FIELD_MAP = {\n")
        for k, v in sorted(cerfa_field_map.items()):
            f.write(f'    "{k}": "{v}",\n')
        f.write("}\n")

    (f"\n✅ CERFA_FIELD_MAP sauvegardé dans : {output_path}")
    ("⚠️ Vérifie et corrige manuellement les champs vides ou incohérents.")

# ============================================================
# ▶️ Exécution directe
# ============================================================
if __name__ == "__main__":
    args = sys.argv[1:]
    if "--scan" in args:
        fields = extract_pdf_fields()
        ("\nCERFA_FIELD_MAP = {")
        for field in fields:
            (f'    "{field}": "",')
        ("}")
    elif "--dry-run" in args:
        generate_field_map(dry_run=True)
    else:
        generate_field_map(dry_run=False)
   