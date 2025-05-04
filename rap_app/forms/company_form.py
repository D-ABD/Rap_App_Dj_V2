from django import forms
from ..models.company import Company

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = [
            'name', 'street_name', 'zip_code', 'city', 'country',
            'contact_name', 'contact_email', 'contact_phone_number', 'contact_job',
            'sector_name', 'actions', 'action_description',
            'website', 'social_network_url'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'sector_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
