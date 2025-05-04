from django import forms
from ..models.prospection import Prospection

class ProspectionForm(forms.ModelForm):
    class Meta:
        model = Prospection
        fields = ['company', 'formation', 'statut', 'objectif', 'commentaire', 'responsable']
        widgets = {
            'commentaire': forms.Textarea(attrs={'rows': 3}),
        }
