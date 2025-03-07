from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import now
from django.core.mail import send_mail

from .forms import  UserRegistrationForm,LoginForm,PasswordResetRequestForm,PasswordResetForm,UserUpdateForm
from .models import User

def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  
            user.save()
            user.generate_confirmation_token()  

            confirmation_url = request.build_absolute_uri(
                f"/users/confirm-email/{user.confirmation_token}/"
            )
            send_mail(
                "Confirmez votre adresse e-mail",
                f"Cliquez ici pour confirmer votre email : {confirmation_url}",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
            )
            messages.success(
                request, "Votre compte a été créé. Vérifiez votre email pour confirmer."
            )
            return redirect("users:login")
    else:
        form = UserRegistrationForm()
    return render(request, "users/register.html", {"form": form})

def custom_login(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_page = request.GET.get("next", "events:list")
            messages.success(request, "Bienvenue, vous êtes connecté !")
            return redirect(next_page)
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
    else:
        form = LoginForm()
    return render(request, "users/login.html", {"form": form})

def confirm_email(request, token):
    user = get_object_or_404(User, confirmation_token=token)
    user.email_confirmed = True
    user.is_active = True
    user.confirmation_token = ""
    user.save()
    messages.success(request, "Votre email a été confirmé. Vous pouvez vous connecter.")
    return redirect("users:login")

@login_required
def profile(request):
    user = request.user
    context = {
        'user': user,
        'profile': user.profile,  
    }
    return render(request, 'users/profile.html', context)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre profil a été mis à jour avec succès.')
            return redirect('users:profile')
    else:
        form = UserUpdateForm(instance=request.user)
    return render(request, 'users/edit_profile.html', {'form': form})

@login_required
def change_password(request):
    from django.contrib.auth.forms import PasswordChangeForm  
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Votre mot de passe a été modifié avec succès.")
            return redirect("users:profile")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "users/change_password.html", {"form": form})

def request_password_reset(request):
    if request.method == "POST":
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            try:
                user = User.objects.get(email=email)
                user.generate_password_reset_token()  
                reset_url = request.build_absolute_uri(
                    f"/users/password-reset/{user.reset_password_token}/"
                )
                send_mail(
                    "Réinitialisation de votre mot de passe",
                    f"Cliquez ici pour réinitialiser votre mot de passe : {reset_url}",
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                )
                messages.success(request, "Un email de réinitialisation a été envoyé.")
            except User.DoesNotExist:
                messages.error(request, "Aucun compte trouvé avec cet email.")
            return redirect("users:login")
    else:
        form = PasswordResetRequestForm()
    return render(request, "users/request_password_reset.html", {"form": form})


def reset_password(request, token):
    try:
        user = User.objects.get(reset_password_token=token)
        if user.reset_token_expires_at and user.reset_token_expires_at < now():
            messages.error(request, "Le lien de réinitialisation a expiré.")
            return redirect("users:request_password_reset")
    except User.DoesNotExist:
        messages.error(request, "Lien de réinitialisation invalide.")
        return redirect("users:request_password_reset")

    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data["new_password"]
            user.set_password(new_password)
            user.reset_password_token = None
            user.reset_token_expires_at = None
            user.save()
            messages.success(request, "Votre mot de passe a été réinitialisé.")
            return redirect("users:login")
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = PasswordResetForm()
    return render(request, "users/reset_password.html", {"form": form, "token": token})

def logout_view(request):
    logout(request)
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return redirect("users:login")
