from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string

User = get_user_model()


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Mot de passe'
        }),
        min_length=8
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Confirmation du mot de passe'
        }),
        min_length=8
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password', 'confirm_password', 'role','profile_image']
        labels = {
            'first_name': 'Nom',
            'last_name': 'Prénom',
            'username': 'Nom d’utilisateur',
            'email': 'Adresse email',
            'role': 'Rôle',
            'password': 'Mot de passe',
            'confirm_password': 'Confirmation du mot de passe',
            'profile_image':'photo de profil'
        }
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Votre nom'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Votre prénom'
            }),
            'username': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Nom d’utilisateur'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Votre adresse email'
            }),
           'profile_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Cet email est déjà utilisé.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            raise ValidationError("Les mots de passe ne correspondent pas.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.confirmation_token = get_random_string(length=64)
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "placeholder": "Email",
            "class": "form-control"
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "placeholder": "Mot de passe",
            "class": "form-control"
        })
    )
class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField()

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise ValidationError("Aucun compte trouvé avec cet e-mail.")
        return email

class PasswordResetForm(forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput, min_length=8)
    confirm_password = forms.CharField(widget=forms.PasswordInput, min_length=8)

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password and confirm_password and new_password != confirm_password:
            raise ValidationError("Les mots de passe ne correspondent pas.")

        return cleaned_data

class UserUpdateForm(forms.ModelForm):
    additional_info = forms.CharField(
        widget=forms.Textarea(attrs={"placeholder": "Informations complémentaires"}),
        required=False,
        label="Informations complémentaires"
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'profile_image']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'profile'):
            self.fields['additional_info'].initial = self.instance.profile.additional_info

    def save(self, commit=True):
        user = super().save(commit)
        additional_info = self.cleaned_data.get('additional_info', '')
        profile = user.profile
        profile.additional_info = additional_info
        if commit:
            profile.save()
        return user
