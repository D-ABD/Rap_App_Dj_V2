import os
from datetime import date, datetime
from pdfrw import PdfReader, PdfWriter, PdfDict, PdfName, PdfObject
from django.conf import settings
from .constants_cerfa import CERFA_FIELD_MAP


def format_value(value):
    """Formate proprement la valeur pour le CERFA."""
    if isinstance(value, (datetime, date)):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, bool):
        return "Oui" if value else "Non"
    return str(value or "").strip() 

 
def generer_pdf_cerfa(cerfa_contrat, output_path=None, flatten=False):
    """
    Remplit le CERFA 10103*14 avec les champs du modèle CerfaContrat.
    Force l’apparence des champs (sinon texte invisible dans Acrobat).
    """
    # 1️⃣ Chemin du modèle
    template_path = os.path.join(settings.BASE_DIR, "rap_app/static/cerfa/cerfa_10103-14.pdf")
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Fichier CERFA introuvable : {template_path}")

    # 2️⃣ Sortie
    if output_path is None:
        output_dir = os.path.join(settings.MEDIA_ROOT, "cerfa_remplis")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"cerfa_{cerfa_contrat.id}.pdf")

    # 3️⃣ Préparation des données
    data = {}
    for pdf_field, model_field in CERFA_FIELD_MAP.items():
        if not model_field:
            continue
        raw_value = getattr(cerfa_contrat, model_field, "")
        data[pdf_field] = format_value(raw_value)

    # 4️⃣ Lecture du template
    template_pdf = PdfReader(template_path)

    # 🔧 Ajout du flag "NeedAppearances"
    if template_pdf.Root:
        template_pdf.Root.AcroForm.update(PdfDict(NeedAppearances=PdfObject("true")))

    # 5️⃣ Injection des champs
    for page in template_pdf.pages:
        if not page.Annots:
            continue
        for annot in page.Annots:
            field_name = getattr(annot.T, "to_unicode", lambda: None)()
            if not field_name:
                continue
            if field_name in data:
                value = data[field_name]
                annot.update(
                    PdfDict(
                        V=PdfObject(f"({value})"),
                        Ff=1,
                        AP=None
                    )
                )

    # 6️⃣ Sauvegarde du PDF
    PdfWriter().write(output_path, template_pdf)

    (f"✅ PDF CERFA généré (visible) : {output_path}")
    return output_path
 