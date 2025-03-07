import uuid
from django.conf import settings
from django.db import models


class Category(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class Event(models.Model):
    STATUS_CHOICES = (
        ('public', 'Public'),
        ('private', 'Privé'),
    )
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='event_images/', null=True, blank=True)
    location = models.CharField(max_length=255)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    capacity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='public')
    organizer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='organized_events')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='events')
    is_free = models.BooleanField(default=False)
    is_private = models.BooleanField(default=False)

    def __str__(self):
        return self.title
    

class Ticket(models.Model):
    TICKET_TYPE_CHOICES = (
        ('free', 'Gratuit'),
        ('paid', 'Payant'),
    )
    
    PAYMENT_STATUS_CHOICES = (
        ('pending', '⏳ En attente'),
        ('completed', '✅ Payé'),
        ('canceled', '❌ Annulé'),
        ('failed', '⚠️ Échec'),
    )

    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tickets')
    event = models.ForeignKey('events.Event', on_delete=models.CASCADE, related_name='tickets')
    ticket_type = models.CharField(max_length=20, choices=TICKET_TYPE_CHOICES)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    qr_code = models.ImageField(upload_to='qr_codes/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"🎟️ Ticket de {self.user} pour {self.event} ({self.get_payment_status_display()})"


class Payment(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    transaction_ref = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"Paiement de {self.amount} par {self.user} le {self.payment_date}"

class Invitation(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='invitations')
    email = models.EmailField()
    token = models.CharField(max_length=64, unique=True)
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invitation pour {self.email} à {self.event.title}"


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.title} - {self.timestamp}"

    def mark_as_read(self):
        self.is_read = True
        self.save()
