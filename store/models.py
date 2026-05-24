from decimal import Decimal

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

# Create your models here.
PLATFORM_CHOICES = (
    ('twitter', 'Twitter'),
    ('facebook', 'Facebook'),
    ('instagram', 'Instagram'),
    ('linkedin', 'LinkedIn'),
    ('youtube', 'YouTube'),
    ('tiktok', 'TikTok'),
    # ('other', 'Other'),
)


STATUS_CHOICES = (
    ('pending', 'Pending'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
)

TRANSACTION_TYPE_CHOICES = (
    ('deposit', 'Deposit'),
    ('withdrawal', 'Withdrawal'),
)
class Service(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    provider_service_id = models.CharField(max_length=255)  # ID used by the provider's API
    price_per_k = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    min = models.IntegerField(default=0)
    max = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def price(self):
        return (self.price_per_k or Decimal('0.00')) / Decimal('1000')
    

class Order(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    target_link = models.URLField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    provider_order_id = models.CharField(max_length=255, blank=True, null=True)
    provider_status = models.CharField(
        max_length=100,
        default="pending",
        choices=STATUS_CHOICES
    )
    provider_response = models.JSONField(
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order #{self.id} - {self.service.name} x {self.quantity} for {self.user.email}"
    
    def count_completed_orders(self):
        return Order.objects.filter(user=self.user, status='completed').count()
    
class TextToSpeechRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    language = models.CharField(max_length=50, default='en')
    voice = models.CharField(max_length=50, default='default')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    audio_file = models.FileField(upload_to='tts_outputs/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"TTS Request #{self.id} for {self.user.email}"
    
# model for social media accounts
class SocialMediaAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES)
    username = models.CharField(max_length=255)
    access_pswd = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.platform}: {self.username}"
    
class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)  # e.g., 'deposit', 'withdrawal'
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reference = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type.title()} of ${self.amount} for {self.user.email}"
    

class Payment(models.Model):
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="payments"
    )

    tx_ref = models.CharField(
        max_length=255,
        unique=True
    )

    transaction_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    currency = models.CharField(
        max_length=10,
        default="NGN"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    gateway_response = models.JSONField(
        blank=True,
        null=True
    )

    verified_at = models.DateTimeField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)