import os
import json
import csv
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from io import BytesIO
from pdfrw import PdfReader, PdfWriter, PageMerge
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from pdf2image import convert_from_path


def _mk_overlay(width, height, labels):
    """Crée un overlay PDF avec les noms de champs et labels proches."""
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(width, height))
    c.setFont("Helvetica-Bold", 7)
    for x, y, text in labels:
        c.setFillColorRGB(1, 1, 1)
        c.rect(x - 1, y - 1, len(text) * 3.3, 7, fill=True, stroke=False)
        c.setFillColor(colors.red)
        c.drawString(x, y + 3, text)
    c.save()
    buf.seek(0)
    return PdfReader(buf)


def extract_labels_from_pdf(pdf_path):
    """Extrait le texte vectoriel visible dans le PDF (non OCR)."""
    labels_by_page = {}
    doc = fitz.open(pdf_path)
    for page_number, page in enumerate(doc, start=1):
        labels = []
        for block in page.get_text("blocks"):
            x1, y1, x2, y2, text, *_ = block
            text = text.strip()
            if text:
                labels.append({
                    "text": text,
                    "x": x1,
                    "y": y1,
                    "x2": x2,
                    "y2": y2,
                })
        labels_by_page[page_number] = labels
    return labels_by_page


def ocr_label_near_field(image, rect, margin=80, lang="fra"):
    """OCR autour du champ pour trouver le texte le plus proche."""
    x1, y1, x2, y2 = rect
    crop_box = (
        max(x1 - margin, 0),
        max(y1 - margin, 0),
        x2 + margin,
        y2 + margin
    )
    cropped = image.crop(crop_box)
    ocr_text = pytesseract.image_to_string(cropped, lang=lang)
    lines = [l.strip() for l in ocr_text.splitlines() if l.strip()]
    # Prend la ligne la plus proche visuellement (souvent la première lisible)
    return lines[0] if lines else None


def find_nearest_label(field_rect, labels, max_vertical=60, max_horizontal=80):
    """Cherche le label texte vectoriel le plus proche du champ."""
    x1, y1, x2, y2 = field_rect
    center_x = (x1 + x2) / 2
    candidates = []

    for lbl in labels:
        text = lbl["text"].strip()
        if not text or len(text) > 60:
            continue
        lower = text.lower()

        if any(skip in lower for skip in [
            "apprenti", "employeur", "maître", "code idcc", "cerfa", "page", "notice",
            "reportez-vous", "familles", "diplôme", "formation", "rémunération"
        ]):
            continue
        if text.isupper() and len(text) > 3:
            continue

        if lbl["y"] > y2 and abs(lbl["y"] - y2) < max_vertical:
            dist = abs(lbl["y"] - y2) + abs(center_x - (lbl["x"] + lbl["x2"]) / 2)
            candidates.append((dist, text))
        elif lbl["x2"] < x1 and abs((lbl["y"] + lbl["y2"]) / 2 - (y1 + y2) / 2) < max_horizontal:
            dist = abs(x1 - lbl["x2"]) + abs((lbl["y"] + lbl["y2"]) / 2 - (y1 + y2) / 2)
            candidates.append((dist, text))

    if not candidates:
        return None
    candidates.sort(key=lambda c: c[0])
    return candidates[0][1]


def make_pdf_field_overlay(template_path, output_pdf, output_json=None, output_csv=None):
    """Crée le PDF annoté + export JSON + CSV avec labels correspondants (texte + OCR)."""
    pdf = PdfReader(template_path)
    static_labels = extract_labels_from_pdf(template_path)
    images = convert_from_path(template_path, dpi=300)
    all_fields = []

    for page_idx, page in enumerate(pdf.pages, start=1):
        labels = []
        annots = getattr(page, "Annots", []) or []
        page_labels = static_labels.get(page_idx, [])
        page_img = images[page_idx - 1].convert("RGB")

        for annot in annots:
            raw_name = getattr(annot, "T", None)
            if raw_name is None and "/T" in annot:
                raw_name = annot["/T"]

            if hasattr(raw_name, "to_unicode"):
                name = raw_name.to_unicode()
            elif isinstance(raw_name, str):
                name = raw_name
            else:
                name = str(raw_name) if raw_name else ""

            rect = annot.Rect
            if not rect or len(rect) != 4:
                continue

            x1, y1, x2, y2 = [float(v) for v in rect]

            # 1️⃣ Cherche d'abord dans le texte vectoriel
            label_text = find_nearest_label((x1, y1, x2, y2), page_labels)
            # 2️⃣ Si aucun label trouvé, OCR autour de la zone
            if not label_text:
                label_text = ocr_label_near_field(page_img, (x1, y1, x2, y2))

            combined_label = f"{name} ({label_text or '❓'})"
            labels.append((x1, y2 + 2, combined_label))

            all_fields.append({
                "page": page_idx,
                "pdf_name": name,
                "label_text": label_text or "",
                "coords": [x1, y1, x2, y2],
                "width": round(x2 - x1, 2),
                "height": round(y2 - y1, 2),
            })

        if labels:
            mb = page.MediaBox
            w, h = float(mb[2]) - float(mb[0]), float(mb[3]) - float(mb[1])
            overlay = _mk_overlay(w, h, labels)
            PageMerge(page).add(overlay.pages[0]).render()

    PdfWriter().write(output_pdf, pdf)
    (f"✅ Overlay PDF généré → {output_pdf}")

    if output_json:
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(all_fields, f, indent=2, ensure_ascii=False)
        (f"✅ Export JSON généré → {output_json}")

    if output_csv:
        with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=["page", "pdf_name", "label_text"])
            writer.writeheader()
            for row in all_fields:
                writer.writerow({
                    "page": row["page"],
                    "pdf_name": row["pdf_name"],
                    "label_text": row["label_text"],
                })
        (f"✅ Export CSV généré → {output_csv}")

    (f"📊 Total champs détectés : {len(all_fields)}")


if __name__ == "__main__":
    BASE = os.path.dirname(__file__)
    tpl = os.path.abspath(os.path.join(BASE, "../static/cerfa/cerfa_10103-14.pdf"))
    out_pdf = os.path.abspath(os.path.join(BASE, "../static/cerfa/cerfa_10103-14_DEBUG.pdf"))
    out_json = os.path.abspath(os.path.join(BASE, "../static/cerfa/cerfa_10103-14_FIELDS.json"))
    out_csv = os.path.abspath(os.path.join(BASE, "../static/cerfa/cerfa_10103-14_FIELDS.csv"))

    if not os.path.exists(tpl):
        (f"❌ Fichier modèle introuvable : {tpl}")
    else:
        make_pdf_field_overlay(tpl, out_pdf, out_json, out_csv)
