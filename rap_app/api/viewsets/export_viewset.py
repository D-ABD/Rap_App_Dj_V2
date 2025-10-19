from django.utils import timezone as dj_timezone
from django.http import HttpResponse
from django.template.loader import render_to_string
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from weasy import HTML
import csv

from ...models.commentaires_appairage import CommentaireAppairage

from ...models.appairage import Appairage
from ...models.partenaires import Partenaire
from ...models.formations import Formation
from ...models.candidat import Candidat
from ..permissions import IsStaffOrAbove


class ExportViewSet(viewsets.ViewSet):
    """
    ViewSet centralisé pour gérer différents exports.
    Chaque action correspond à un domaine (appairages, partenaires, formations, candidats…).
    """

    permission_classes = [IsAuthenticated, IsStaffOrAbove]

    # ---------------- APPARIAGES ----------------
    @action(detail=False, methods=["get"], url_path="appairages-csv")
    def appairages_csv(self, request):
        qs = Appairage.objects.all().select_related("candidat", "partenaire", "formation")

        response = HttpResponse(content_type="text/csv; charset=utf-8")
        filename = f'appairages_{dj_timezone.now().strftime("%Y%m%d_%H%M%S")}.csv'
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        writer = csv.writer(response)

        writer.writerow(["id", "candidat", "partenaire", "formation", "statut", "date_appairage"])
        for a in qs:
            writer.writerow([
                a.id,
                getattr(a.candidat, "nom_complet", ""),
                getattr(a.partenaire, "nom", ""),
                getattr(a.formation, "nom", ""),
                a.get_statut_display(),
                a.date_appairage.isoformat() if a.date_appairage else "",
            ])

        return response

    @action(detail=False, methods=["get"], url_path="appairages-pdf")
    def appairages_pdf(self, request):
        qs = Appairage.objects.all().select_related("candidat", "partenaire", "formation")
        html_string = render_to_string("exports/appairages_pdf.html", {"appairages": qs})
        pdf = HTML(string=html_string).write_pdf()

        response = HttpResponse(pdf, content_type="application/pdf")
        filename = f'appairages_{dj_timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    # ---------------- PARTENAIRES ----------------
    @action(detail=False, methods=["get"], url_path="partenaires-csv")
    def partenaires_csv(self, request):
        qs = Partenaire.objects.all()

        response = HttpResponse(content_type="text/csv; charset=utf-8")
        filename = f'partenaires_{dj_timezone.now().strftime("%Y%m%d_%H%M%S")}.csv'
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        writer = csv.writer(response)

        writer.writerow(["id", "nom", "type", "email", "telephone"])
        for p in qs:
            writer.writerow([
                p.id,
                p.nom,
                p.get_type_display(),
                p.contact_email,
                p.contact_telephone,
            ])

        return response

    # ---------------- FORMATIONS ----------------
    @action(detail=False, methods=["get"], url_path="formations-csv")
    def formations_csv(self, request):
        qs = Formation.objects.all().select_related("centre", "type_offre")

        response = HttpResponse(content_type="text/csv; charset=utf-8")
        filename = f'formations_{dj_timezone.now().strftime("%Y%m%d_%H%M%S")}.csv'
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        writer = csv.writer(response)

        writer.writerow(["id", "nom", "centre", "type_offre", "statut"])
        for f in qs:
            writer.writerow([
                f.id,
                f.nom,
                getattr(f.centre, "nom", ""),
                getattr(f.type_offre, "libelle", ""),
                f.get_statut_display(),
            ])

        return response

    # ---------------- CANDIDATS ----------------
    @action(detail=False, methods=["get"], url_path="candidats-csv")
    def candidats_csv(self, request):
        qs = Candidat.objects.select_related("formation", "formation__centre").all()

        response = HttpResponse(content_type="text/csv; charset=utf-8")
        filename = f'candidats_{dj_timezone.now().strftime("%Y%m%d_%H%M%S")}.csv'
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        writer = csv.writer(response)

        writer.writerow([
            "id",
            "nom",
            "prenom",
            "email",
            "telephone",
            "ville",
            "code_postal",
            "formation",
            "centre",
            "statut",
            "cv_statut",
        ])

        for c in qs:
            writer.writerow([
                c.id,
                c.nom,
                c.prenom,
                c.email,
                c.telephone,
                c.ville,
                c.code_postal,
                getattr(c.formation, "nom", "") if c.formation else "",
                getattr(c.formation.centre, "nom", "") if c.formation and c.formation.centre else "",
                c.get_statut_display() if hasattr(c, "get_statut_display") else (c.statut or ""),
                c.get_cv_statut_display() if hasattr(c, "get_cv_statut_display") else (c.cv_statut or ""),
            ])

        return response

    @action(detail=False, methods=["get"], url_path="candidats-pdf")
    def candidats_pdf(self, request):
        qs = Candidat.objects.select_related("formation", "formation__centre").all()
        html_string = render_to_string("exports/candidats_pdf.html", {"candidats": qs})
        pdf = HTML(string=html_string).write_pdf()

        response = HttpResponse(pdf, content_type="application/pdf")
        filename = f'candidats_{dj_timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

 # ---------------- COMMENTAIRES APPAIRAGES ----------------
    @action(detail=False, methods=["get"], url_path="commentaires-appairages-csv")
    def commentaires_appairages_csv(self, request):
        qs = CommentaireAppairage.objects.select_related(
            "appairage",
            "appairage__candidat",
            "appairage__partenaire",
            "appairage__formation",
            "created_by",
        ).all()

        response = HttpResponse(content_type="text/csv; charset=utf-8")
        filename = f'commentaires_appairages_{dj_timezone.now().strftime("%Y%m%d_%H%M%S")}.csv'
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        writer = csv.writer(response)

        writer.writerow([
            "id",
            "appairage_id",
            "candidat",
            "partenaire",
            "formation",
            "body",
            "created_by",
            "created_at",
            "updated_by",
            "updated_at",
        ])

        for c in qs:
            writer.writerow([
                c.id,
                getattr(c.appairage, "id", ""),
                getattr(c.appairage.candidat, "nom_complet", "") if c.appairage and c.appairage.candidat else "",
                getattr(c.appairage.partenaire, "nom", "") if c.appairage and c.appairage.partenaire else "",
                getattr(c.appairage.formation, "nom", "") if c.appairage and c.appairage.formation else "",
                c.body,
                getattr(c.created_by, "username", "") if c.created_by else "",
                c.created_at.isoformat() if c.created_at else "",
                getattr(c.updated_by, "username", "") if c.updated_by else "",
                c.updated_at.isoformat() if c.updated_at else "",
            ])

        return response

    @action(detail=False, methods=["get"], url_path="commentaires-appairages-pdf")
    def commentaires_appairages_pdf(self, request):
        qs = CommentaireAppairage.objects.select_related(
            "appairage",
            "appairage__candidat",
            "appairage__partenaire",
            "appairage__formation",
            "created_by",
        ).all()

        html_string = render_to_string("exports/commentaires_appairages_pdf.html", {"commentaires": qs})
        pdf = HTML(string=html_string).write_pdf()

        response = HttpResponse(pdf, content_type="application/pdf")
        filename = f'commentaires_appairages_{dj_timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response