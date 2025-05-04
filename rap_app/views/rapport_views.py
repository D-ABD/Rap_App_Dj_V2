from django.views.generic import ListView, DetailView, FormView, DeleteView
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
import logging
import json

from ..models.rapports import Rapport
from ..models import Centre, TypeOffre, Statut
from ..services.generateur_rapports import GenerateurRapport
from ..forms.rapports_forms import RapportCreationForm


import csv
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors


logger = logging.getLogger(__name__)

class RapportListView(LoginRequiredMixin, ListView):
    """Vue pour afficher la liste des rapports générés."""
    model = Rapport
    template_name = 'rapports/rapport_list.html'
    context_object_name = 'rapports'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()

        type_rapport = self.request.GET.get('type_rapport')
        periode = self.request.GET.get('periode')

        if type_rapport:
            queryset = queryset.filter(type_rapport=type_rapport)
        if periode:
            queryset = queryset.filter(periode=periode)

        return queryset


class RapportDetailView(LoginRequiredMixin, DetailView):
    """Vue pour afficher un rapport détaillé."""
    model = Rapport
    template_name = 'rapports/rapport_detail.html'
    context_object_name = 'rapport'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rapport = self.get_object()

        try:
            if isinstance(rapport.donnees, str):
                rapport.donnees = json.loads(rapport.donnees)
            context['donnees'] = rapport.donnees
        except json.JSONDecodeError as e:
            logger.error(f"❌ Erreur de décodage JSON pour le rapport {rapport.id}: {e}")
            context['donnees'] = {}

        return context


class RapportCreationView(LoginRequiredMixin, FormView):
    """Vue pour créer un nouveau rapport."""
    template_name = 'rapports/rapport_form.html'
    form_class = RapportCreationForm
    success_url = reverse_lazy('rapport-list')

    def form_valid(self, form):
        try:
            rapport = GenerateurRapport.generer_rapport(
                type_rapport=form.cleaned_data['type_rapport'],
                date_debut=form.cleaned_data['date_debut'],
                date_fin=form.cleaned_data['date_fin'],
                centre=form.cleaned_data.get('centre'),
                type_offre=form.cleaned_data.get('type_offre'),
                statut=form.cleaned_data.get('statut'),
                format=form.cleaned_data.get('format', Rapport.FORMAT_HTML),
                utilisateur=self.request.user,
                periode=form.cleaned_data.get('periode')
            )

            if rapport:
                messages.success(self.request, f'✅ Rapport "{rapport.nom}" généré avec succès.')
            else:
                messages.error(self.request, "❌ Erreur lors de la génération du rapport.")

        except Exception as e:
            logger.exception(f"Erreur lors de la création du rapport: {str(e)}")
            messages.error(self.request, f'Erreur lors de la génération du rapport: {str(e)}')

        return super().form_valid(form)


    def _export_pdf(self, rapport):
        """Logique d'export PDF"""
        try:
            from io import BytesIO
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas

            buffer = BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            p.drawString(100, 750, f"Rapport: {rapport.nom}")
            p.drawString(100, 730, f"Type: {rapport.get_type_rapport_display()}")
            p.drawString(100, 710, f"Date: {rapport.date_debut} - {rapport.date_fin}")
            p.drawString(100, 690, f"Généré par: {rapport.utilisateur}")

            y_position = 670
            for formation in rapport.donnees.get('formations', []):
                p.drawString(100, y_position, f"Formation: {formation['nom']} - {formation['taux_remplissage']}%")
                y_position -= 20

            p.showPage()
            p.save()
            buffer.seek(0)

            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{rapport.nom}.pdf"'
            return response
        except Exception as e:
            logger.exception(f"Erreur lors de l'export PDF: {str(e)}")
            messages.error(self.request, "Erreur lors de l'export PDF.")
            return redirect('rapport-detail', pk=rapport.pk)

    def _export_excel(self, rapport):
        """Logique d'export Excel"""
        try:
            import pandas as pd

            formations_data = rapport.donnees.get('formations', [])
            df = pd.DataFrame(formations_data)

            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename="{rapport.nom}.xlsx"'
            df.to_excel(response, index=False)
            return response
        except Exception as e:
            logger.exception(f"Erreur lors de l'export Excel: {str(e)}")
            messages.error(self.request, "Erreur lors de l'export Excel.")
            return redirect('rapport-detail', pk=rapport.pk)

    def _export_csv(self, rapport):
        """Logique d'export CSV"""
        try:
            import csv
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{rapport.nom}.csv"'

            writer = csv.writer(response)
            formations_data = rapport.donnees.get('formations', [])
            if formations_data:
                writer.writerow(formations_data[0].keys())
                for formation in formations_data:
                    writer.writerow(formation.values())

            return response
        except Exception as e:
            logger.exception(f"Erreur lors de l'export CSV: {str(e)}")
            messages.error(self.request, "Erreur lors de l'export CSV.")
            return redirect('rapport-detail', pk=rapport.pk)
        


# ✅ VUE DE SUPPRESSION D'UN RAPPORT
class RapportDeleteView(LoginRequiredMixin, DeleteView):
    """Vue pour supprimer un rapport."""
    model = Rapport
    template_name = 'rapports/rapport_confirm_delete.html'
    success_url = reverse_lazy('rapport-list')

    def delete(self, request, *args, **kwargs):
        """Supprime le rapport et affiche un message de confirmation."""
        rapport = self.get_object()
        messages.success(request, f'🚮 Rapport "{rapport.nom}" supprimé avec succès.')
        return super().delete(request, *args, **kwargs)


# ✅ VUE POUR EXPORTER UN RAPPORT DANS DIFFÉRENTS FORMATS
class RapportExportView(LoginRequiredMixin, DetailView):
    """Vue pour exporter un rapport dans différents formats."""
    model = Rapport

    def get(self, request, *args, **kwargs):
        rapport = self.get_object()
        format_export = request.GET.get('format', rapport.format)

        if format_export == Rapport.FORMAT_PDF:
            return self._export_pdf(rapport)
        elif format_export == Rapport.FORMAT_EXCEL:
            return self._export_excel(rapport)
        elif format_export == Rapport.FORMAT_CSV:
            return self._export_csv(rapport)
        else:
            messages.error(request, "⚠ Format d'export non valide.")
            return redirect('rapport-detail', pk=rapport.pk)

    def _export_pdf(self, rapport):
        """Export du rapport en PDF."""
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            data = [["Formation", "Taux remplissage"]]

            for formation in rapport.donnees.get('formations', []):
                data.append([formation['nom'], f"{formation['taux_remplissage']}%"])

            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))

            doc.build([table])
            buffer.seek(0)

            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{rapport.nom}.pdf"'
            return response

        except Exception as e:
            logger.exception(f"❌ Erreur lors de l'export PDF: {str(e)}")
            messages.error(self.request, "Erreur lors de l'export PDF.")
            return redirect('rapport-detail', pk=rapport.pk)

    def _export_excel(self, rapport):
        """Export du rapport en Excel."""
        try:
            formations_data = rapport.donnees.get('formations', [])
            if not formations_data:
                messages.error(self.request, "⚠ Le rapport ne contient pas de données à exporter.")
                return redirect('rapport-detail', pk=rapport.pk)

            df = pd.DataFrame(formations_data)
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename="{rapport.nom}.xlsx"'
            df.to_excel(response, index=False)
            return response

        except Exception as e:
            logger.exception(f"❌ Erreur lors de l'export Excel: {str(e)}")
            messages.error(self.request, "Erreur lors de l'export Excel.")
            return redirect('rapport-detail', pk=rapport.pk)

    def _export_csv(self, rapport):
        """Export du rapport en CSV."""
        try:
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{rapport.nom}.csv"'
            writer = csv.writer(response)

            formations_data = rapport.donnees.get('formations', [])
            if formations_data:
                writer.writerow(formations_data[0].keys())  # Écrire l'en-tête
                for formation in formations_data:
                    writer.writerow(formation.values())

            return response

        except Exception as e:
            logger.exception(f"❌ Erreur lors de l'export CSV: {str(e)}")
            messages.error(self.request, "Erreur lors de l'export CSV.")
            return redirect('rapport-detail', pk=rapport.pk)

