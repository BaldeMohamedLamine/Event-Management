from django.contrib.auth.models import BaseUserManager, AbstractUser
from django.db import models
import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.crypto import get_random_string
from django.utils import timezone
from datetime import timedelta

class UserManager(BaseUserManager):
    def get_by_natural_key(self, email):
        return self.get(email=email)

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'utilisateur doit avoir une adresse e-mail")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ROLE_CHOICES = (
        ('organisator', 'Organisateur'),
        ('participant', 'Participant'),
    )
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=40)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='participant')
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    email_confirmed = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    confirmation_token = models.CharField(max_length=64, blank=True, null=True)
    reset_password_token = models.CharField(max_length=64, blank=True, null=True)
    reset_token_expires_at = models.DateTimeField(blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = UserManager() 

    def generate_confirmation_token(self):
        self.confirmation_token = get_random_string(length=64)
        self.save()
    
    def generate_password_reset_token(self):
        self.reset_password_token = get_random_string(length=64)
        self.reset_token_expires_at = timezone.now() + timedelta(hours=1)
        self.save()
    
    def is_organisator(self):
        return self.role == 'organisator'

    def is_participant(self):
        return self.role == 'participant'

    def __str__(self):
        return self.username
    
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    additional_info = models.TextField(blank=True, null=True)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if not hasattr(instance, 'profile'):
        Profile.objects.create(user=instance)
    instance.profile.save()
