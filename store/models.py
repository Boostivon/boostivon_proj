from decimal import Decimal

from django.db import models
from django.contrib.auth import get_user_model
import uuid
import random
import string


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
    
    def order_count(self):
        return Order.objects.filter(service=self)

class Order(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='orders')
    quantity = models.IntegerField()
    target_link = models.URLField(max_length=1000)
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
    
    def orders_count(self):
        return Order.objects.filter(user=self.user).count() 
   
class TextToSpeechRequest(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
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
class Platform(models.Model):
    icon = models.ImageField(upload_to='platform_icons/', blank=True, null=True)
    name = models.CharField(max_length=50, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    description = models.TextField(blank=True)
    quantity = models.IntegerField(default=0)  # New field to track quantity of accounts available
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name
    
    def accounts_count(self):
        return SocialMediaAccount.objects.filter(platform=self, is_assigned=False).count()
    
    # calculate quantity of platform based on number of social media accounts available for that platform
    def save(self, *args, **kwargs):
        # Always set `quantity` to the number of unassigned SocialMediaAccount records
        try:
            self.quantity = self.accounts_count()
        except Exception:
            # If something goes wrong (e.g., during initial migration), default to 0
            self.quantity = 0
        super().save(*args, **kwargs)
        
    
class SocialMediaAccount(models.Model):
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE)
    logs = models.TextField(blank=True, null=True)  # Store account credentials or relevant logs
    link = models.URLField(max_length=1000, blank=True, null=True)
    is_assigned = models.BooleanField(default=False)  # New field to track if the account is assigned to a user
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.platform}: {self.logs.split(':')[0] if self.logs else 'No Logs'}"
    
class Transaction(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)  # e.g., 'deposit', 'withdrawal'
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reference = models.CharField(max_length=255, unique=True)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type.title()} of ${self.amount} for {self.user.email}"
    

class Payment(models.Model):
    
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)

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
    
    
class AccountOrder(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='account_orders')
    order_id = models.CharField(max_length=255, unique=True)
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Account Order #{self.id} - {self.platform.name} x {self.quantity} for {self.user.email}"
    
    def save(self, *args, **kwargs):
        # On save, update the total price based on the platform price and quantity
        self.total_price = self.platform.price * self.quantity
        if not self.order_id:
            # generate a unique order ID using uuid4 and a random string
            self.order_id = str(uuid.uuid4())
        super().save(*args, **kwargs)

class UserPlatformAccount(models.Model):
    """Tracks which social media accounts are assigned to which users"""
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='platform_accounts')
    account = models.OneToOneField(SocialMediaAccount, on_delete=models.CASCADE)
    account_order = models.ForeignKey(AccountOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='user_accounts')
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.account}"
    
    class Meta:
        unique_together = ('user', 'account')