# forms.py
from django import forms
from django.utils import timezone

from ..models.centres import Centre
from ..models.vae_jury import SuiviJury, VAE, HistoriqueStatutVAE

class SuiviJuryForm(forms.ModelForm):
    class Meta:
        model = SuiviJury
        fields = ['centre', 'annee', 'mois', 'objectif_jury', 'jurys_realises']
        widgets = {
            'annee': forms.NumberInput(attrs={'min': 2000, 'max': 2100}),
        }

class VAEForm(forms.ModelForm):
    class Meta:
        model = VAE
        fields = ['centre', 'reference', 'date_creation', 'statut', 'commentaire']
        widgets = {
            'date_creation': forms.DateInput(attrs={'type': 'date'}),
            'commentaire': forms.Textarea(attrs={'rows': 4}),
        }

class HistoriqueStatutVAEForm(forms.ModelForm):
    class Meta:
        model = HistoriqueStatutVAE
        fields = ['vae', 'statut', 'date_changement_effectif', 'commentaire']
        widgets = {
            'date_changement_effectif': forms.DateInput(attrs={'type': 'date'}),
            'commentaire': forms.Textarea(attrs={'rows': 4}),
        }
class ObjectifCentreForm(forms.ModelForm):
    class Meta:
        model = Centre
        fields = ['objectif_annuel_jury', 'objectif_mensuel_jury']        