from django import forms
from .models import Event, Category
class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'image', 'location', 'start_date', 'end_date', 'capacity', 'price', 'status', 'category', 'is_free', 'is_private']
        labels = {
            'price': 'Tarif (GNF)',
            'description': 'Description',
            'location': 'Lieu',
            'start_date': 'Date Début',
            'end_date': 'Date Fin',
            'capacity': 'Capacité',
            'status': 'Statut',
            'category': 'Catégorie',
            'is_free': "Événement gratuit ?",
            'is_private': "Événement privé ?"
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titre de l\'événement'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Description', 'rows': 4}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Lieu'}),
            'start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de places'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Prix en GNF'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'is_free': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_private': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
class EventFilterForm(forms.Form):
    date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control border-dark', 'type': 'date', 'placeholder': 'Choisissez une date'}),
        label="Date"
    )
    category = forms.ModelChoiceField(
    queryset=Category.objects.all(),
    required=False,
    label="Catégorie",
    empty_label="Sélectionnez une catégorie",
    widget=forms.Select(attrs={'class': 'form-select border-dark'})
)


    location = forms.CharField(
    max_length=255,
    required=False,
    label="Lieu",
    widget=forms.TextInput(attrs={'class': 'form-control border-dark', 'placeholder': 'Entrez un lieu'})
)


class PaymentForm(forms.Form):
    confirm = forms.BooleanField(required=True, label="Confirmer le paiement")

class EventRegistrationForm(forms.Form):
    pass
