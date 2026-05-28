from datetime import timedelta, timezone
from django.utils import timezone
import secrets

from django.db import models
from django.contrib.auth.models import AbstractUser

from store.models import Order

# Create your models here.
class User(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    email_verified = models.BooleanField(default=False)
    role = models.CharField(max_length=20, default='customer')
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    password_changed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.email
    
    def orders_count(self):
        return Order.objects.filter(user=self).count()

class EmailVerification(models.Model):
    """Model to store email verification codes and track verification status."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_verification')
    code = models.CharField(max_length=6, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=5)
    verified = models.BooleanField(default=False)
    
    def is_valid(self):
        """Check if code is still valid and hasn't exceeded max attempts."""
        return (
            timezone.now() < self.expires_at and 
            self.attempts < self.max_attempts and 
            not self.verified
        )
    
    def increment_attempts(self):
        """Increment failed verification attempts."""
        self.attempts += 1
        self.save()
    
    @classmethod
    def generate_for_user(cls, user, expires_in_minutes=15):
        """Generate a new verification code for a user."""
        code = ''.join(secrets.choice('0123456789') for _ in range(6))
        expires_at = timezone.now() + timedelta(minutes=expires_in_minutes)
        
        # Delete any existing verification for this user
        cls.objects.filter(user=user).delete()
        
        return cls.objects.create(
            user=user,
            code=code,
            expires_at=expires_at
        )
    
    def __str__(self):
        return f"Verification for {self.user.email}"
    
class PasswordReset(models.Model):
    """Model to store password reset tokens and track reset status."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_resets')
    token = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    
    def is_valid(self):
        """Check if token is still valid and hasn't been used."""
        return (
            timezone.now() < self.expires_at and 
            not self.used
        )
    
    @classmethod
    def generate_for_user(cls, user, expires_in_minutes=30):
        """Generate a new password reset token for a user."""
        token = secrets.token_urlsafe(20)
        expires_at = timezone.now() + timedelta(minutes=expires_in_minutes)

        # Invalidate any existing unused tokens for this user so only the latest link works.
        cls.objects.filter(user=user, used=False).update(used=True)
        
        return cls.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )
    
    def __str__(self):
        return f"Password reset for {self.user.email}"