from django.urls import path
from .views import register, custom_login, logout_view, request_password_reset, reset_password,confirm_email
from .views import profile,edit_profile
app_name = "users"

urlpatterns = [
    path("register/", register, name="register"),
    path("login/", custom_login, name="login"),
    path("logout/", logout_view, name="logout"),
    path('confirm-email/<str:token>/', confirm_email, name='confirm_email'),
    path("password-reset-request/", request_password_reset, name="password_reset_request"),
    path("password-reset/<str:token>/", reset_password, name="reset-password"),
    path("profile/", profile, name="profile"),
    path("profile/edit/", edit_profile, name="edit_profile"),
]
