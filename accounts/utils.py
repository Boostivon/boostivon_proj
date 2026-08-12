"""Utility functions for the accounts app."""
from collections.abc import Iterable
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse

from django.http import JsonResponse
import requests
from .models import EmailVerification, PasswordReset
import resend

resend.api_key = settings.RESEND_API_KEY
SMVAULT_API_KEY = settings.SMVAULT_API_KEY

def send_verification_code(user, verification_code):
    """
    Send an email verification code to a user.
    
    Args:
        user: The User instance to send the code to
        verification_code: The 6-digit verification code or EmailVerification instance
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    
    # Handle both string code and EmailVerification instances
    if isinstance(verification_code, EmailVerification):
        code = verification_code.code
    else:
        code = verification_code
    
    subject = "Boostivon Email Verification Code"
    
    # Create HTML email body
    html_message = f"""
    <html>
        <body style="font-family:Arial,sans-serif;margin:20px;background:#0F0F0F;color:#FFFFFF;">
            <div style="max-width: 640px; margin: auto; padding: 24px; border-radius: 18px; background: #1F2937; box-shadow: 0 20px 50px rgba(0, 0, 0, 0.55);">
                <h2 style="margin-top: 0; color: #FBBF24;">Email Verification</h2>
                <p style="color: #D1D5DB;">Hello {user.username},</p>
                <p style="color: #D1D5DB;">Thank you for registering with Boostivon! To complete your registration, please use the following verification code:</p>
                <h1 style="color:#FBBF24;letter-spacing:2px;font-size:2em;margin:30px 0">{code}</h1>
                <p style="color: #D1D5DB;">This code will expire in 15 minutes.</p>
                <p style="color: #D1D5DB;">If you did not create this account, please ignore this email.</p>
                <hr style="border:none;border-top:1px solid rgba(251,191,36,0.2);">
                <p style="color:#D1D5DB;font-size:0.9em;">Boostivon • {settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'boostivon.com'}</p>
            </div>
        </body>
    </html>
    """
    
    plain_message = f"""
Email Verification

Hello {user.username},

Thank you for registering with Boostivon! To complete your registration, please use the following verification code:

{code}

This code will expire in 15 minutes.

If you did not create this account, please ignore this email.

Boostivon
    """
    
    try:
        params: resend.Emails.SendParams = {
            "from": f"Boostivon <{settings.DEFAULT_FROM_EMAIL}>",
            "to": [user.email],
            "subject": subject,
            "html": html_message,
        }
        resend.Emails.send(params)
        return True
    except Exception as e:
        print(f"Failed to send verification email to {user.email}: {str(e)}")
        return False

# send reset password link email with one time token
def send_password_reset_email(request, user, password_reset):
    """Send a one-time password reset email containing a tokenized link."""
    if isinstance(password_reset, PasswordReset):
        token = password_reset.token
    else:
        token = str(password_reset)

    reset_path = reverse('password_reset_confirm', args=[token])
    reset_url = request.build_absolute_uri(reset_path)

    subject = 'Reset Your Boostivon Password'
    html_message = f"""
    <html>
        <body style="font-family:Arial,sans-serif;margin:20px;background:#0F0F0F;color:#FFFFFF;">
            <div style="max-width: 640px; margin: auto; padding: 24px; border-radius: 18px; background: #1F2937; box-shadow: 0 20px 50px rgba(0, 0, 0, 0.55);">
                <h2 style="margin-top: 0; color: #FBBF24;">Password Reset Request</h2>
                <p style="color: #D1D5DB;">Hello {user.username},</p>
                <p style="color: #D1D5DB;">We received a request to reset your Boostivon password. Click the button below to reset it now.</p>
                <p style="text-align:center;margin:30px 0">
                    <a href="{reset_url}" style="display:inline-block;padding:14px 24px;background:#FBBF24;color:#000000;text-decoration:none;border-radius:6px;border:1px solid #D97706;">Reset Password</a>
                </p>
                <p style="color: #D1D5DB;">If the button above does not work, copy and paste this link into your browser:</p>
                <p><a href="{reset_url}" style="color:#FBBF24;">{reset_url}</a></p>
                <p style="color: #D1D5DB;">This link expires in 30 minutes and can only be used once.</p>
                <p style="color: #D1D5DB;">If you did not request a password reset, please ignore this email.</p>
                <hr style="border:none;border-top:1px solid rgba(251,191,36,0.2);">
                <p style="color:#D1D5DB;font-size:0.9em">Boostivon • www.boostivon.com.ng</p>
            </div>
        </body>
    </html>
    """
    plain_message = f"""
Password Reset Request

Hello {user.username},

We received a request to reset your Boostivon password. Use the link below to reset it now:

{reset_url}

This link expires in 30 minutes and can only be used once.

If you did not request a password reset, please ignore this email.

Boostivon
    """
    try:
        params: resend.Emails.SendParams = {
            "from": f"Boostivon <{settings.DEFAULT_FROM_EMAIL}>",
            "to": [user.email],
            "subject": subject,
            "html": html_message,
        }
        resend.Emails.send(params)
        return True
    except Exception as e:
        print(f"Failed to send password reset email to {user.email}: {str(e)}")
        return False

def list_platforms():
        url = f"https://smvaults.com/api/products.php?api_key={SMVAULT_API_KEY}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            products = response.json()["categories"]
            return products
        except requests.RequestException as e:
            print(f"Failed to fetch products from SMVault: {str(e)}")
            return []
        
def get_platform_products(platform_id):
    url = f"https://smvaults.com/api/product.php?api_key={SMVAULT_API_KEY}&product={platform_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        product = response.json()
        return product['product']
    except requests.RequestException as e:
        return (f"Failed to fetch products for platform {platform_id} from SMVault: {str(e)}")

def orders(order_id):
    url = f"https://smvaults.com/api/order.php?api_key={SMVAULT_API_KEY}&order={order_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        orders = response.json()
        return orders
    except requests.RequestException as e:
        return {}
def buy_product(product_id, amount, coupon=""):

    API_KEY = SMVAULT_API_KEY 

    payload = {
        "action": "buyProduct",
        "id": product_id,          # Product ID
        "amount": amount,      # Quantity
        "coupon": coupon,     # Discount code (leave empty if none)
        "api_key": API_KEY
    }

    response = requests.post(
        "https://smvaults.com/api/buy_product",
        data=payload      # form-data
    )

    result = response.json()
    return result
   
def convert_price_to_naira(price_in_dollars):
    """Convert USD amount to NGN using stored ExchangeRate.

    Falls back to calling the external API once if no stored rate exists.
    Returns Decimal or float-like value.
    """
    try:
        from store.utils import get_exchange_rate, update_exchange_rate
        rate = get_exchange_rate('USD', 'NGN')
        # if rate is 1 (fallback) try updating once
        if rate == 1 or rate == '1' or float(rate) == 1.0:
            updated = update_exchange_rate('USD', 'NGN')
            if updated:
                rate = updated
        return float(rate) * float(price_in_dollars)
    except Exception as e:
        print(f"Error converting price: {str(e)}")
        return float(price_in_dollars)
    
def get_product(product_id):
    url = f"https://smvaults.com/api/product.php?api_key={SMVAULT_API_KEY}&product={product_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        product = response.json()
        return product['product']
    except requests.RequestException as e:
        return (f"Failed to fetch product {product_id} from SMVault: {str(e)}")
    

def bulk_email(user, email_subject, email_body):
    """Send a bulk email to one or more users.

    Accepts a single user object, an email string, or an iterable of users/email strings.
    Returns True when the message is queued successfully, otherwise False.
    """

    subject = email_subject or 'Boostivon Update'
    html_message = f"""
    <html>
      <body style="font-family:Arial,sans-serif;margin:20px;background:#0F0F0F;color:#FFFFFF;">
        <div style="max-width:680px;margin:auto;padding:24px;border-radius:18px;background:#1F2937;box-shadow:0 20px 50px rgba(0,0,0,0.55);">
          <h2 style="margin-bottom:0.5rem;color:#FBBF24;">{subject}</h2>
          <div style="margin-bottom:1.5rem;color:#D1D5DB;line-height:1.75;">{email_body}</div>
          <hr style="border:none;border-top:1px solid rgba(251,191,36,0.2);margin:24px 0;" />
          <p style="color:#D1D5DB;font-size:0.9rem;">Boostivon • boostivon.com.ng</p>
        </div>
      </body>
    </html>
    """

    try:
        params: resend.Emails.SendParams = {
            "from": f"Boostivon <{settings.DEFAULT_FROM_EMAIL}>",
            "to": user,
            "subject": subject,
            "html": html_message,
        }
        resend.Emails.send(params)
        return True
    except Exception as e:
        print(f"Failed to send bulk email to {user}: {str(e)}")
        return False

def account_topup_email(user, amount):
    """Send an email notification about an admin account top-up."""
    subject = "Account Top-up Alert"
    body = f"Your account has been topped up with {amount}."
    return bulk_email(user, subject, body)