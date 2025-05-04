from django import forms
from django.utils import timezone
from datetime import timedelta

from ..models.rapports import Rapport
from ..models import Centre, TypeOffre, Statut

class RapportCreationForm(forms.Form):
    """Formulaire pour créer un nouveau rapport."""
    
    type_rapport = forms.ChoiceField(
        choices=Rapport.TYPE_CHOICES,
        label="Type de rapport",
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Sélectionnez le type de rapport à générer."
    )
    
    periode = forms.ChoiceField(
        choices=[("", "Aucune période sélectionnée")] + Rapport.PERIODE_CHOICES,
        label="Périodicité (optionnelle)",
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial=Rapport.PERIODE_MENSUEL,
        help_text="Choisissez la période du rapport (optionnel)."
    )
    
    date_debut = forms.DateField(
        label="Date de début",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        help_text="La date de début de la période du rapport."
    )
    
    date_fin = forms.DateField(
        label="Date de fin",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        help_text="La date de fin de la période du rapport."
    )
    
    centre = forms.ModelChoiceField(
        queryset=Centre.objects.none(),
        label="Centre (optionnel)",
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Filtrer par centre (optionnel)."
    )

    type_offre = forms.ModelChoiceField(
        queryset=TypeOffre.objects.none(),
        label="Type d'offre (optionnel)",
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Filtrer par type d'offre (optionnel)."
    )
    
    statut = forms.ModelChoiceField(
        queryset=Statut.objects.none(),
        label="Statut (optionnel)",
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Filtrer par statut (optionnel)."
    )
    
    format = forms.ChoiceField(
        choices=Rapport.FORMAT_CHOICES,
        label="Format d'export",
        initial=Rapport.FORMAT_HTML,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Choisissez le format d'export du rapport."
    )

    description = forms.CharField(
        label="Description (optionnelle)",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False,
        help_text="Ajoutez une description pour ce rapport (optionnel)."
    )

    def __init__(self, *args, **kwargs):
        """Initialisation dynamique des choix de centres, types d'offres et statuts."""
        super().__init__(*args, **kwargs)

        # Récupérer les données dynamiquement
        self.fields['centre'].queryset = Centre.objects.all().order_by('nom')
        self.fields['type_offre'].queryset = TypeOffre.objects.all().order_by('nom')
        self.fields['statut'].queryset = Statut.objects.all().order_by('nom')

        # Initialisation des dates
        self.fields['date_debut'].initial = timezone.now().date() - timedelta(days=30)
        self.fields['date_fin'].initial = timezone.now().date()

    def clean(self):
        """Validation des dates et autres champs."""
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')

        # Vérifier que la date de début est bien avant la date de fin
        if date_debut and date_fin:
            if date_debut > date_fin:
                self.add_error('date_debut', "⚠ La date de début doit être antérieure à la date de fin.")
                self.add_error('date_fin', "⚠ La date de fin doit être postérieure à la date de début.")

            if date_fin > timezone.now().date():
                self.add_error('date_fin', "⚠ La date de fin ne peut pas être dans le futur.")

        return cleaned_data
