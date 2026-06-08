"""Utility functions for the accounts app."""
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
        <body style="font-family:Arial,sans-serif;margin:20px">
            <h2>Email Verification</h2>
            <p>Hello {user.username},</p>
            <p>Thank you for registering with Boostivon! To complete your registration, please use the following verification code:</p>
            <h1 style="color:#0b76c2;letter-spacing:2px;font-size:2em;margin:30px 0">{code}</h1>
            <p>This code will expire in 15 minutes.</p>
            <p>If you did not create this account, please ignore this email.</p>
            <hr>
            <p style="color:#666;font-size:0.9em">Boostivon • {settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'boostivon.com'}</p>
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
        <body style="font-family:Arial,sans-serif;margin:20px">
            <h2>Password Reset Request</h2>
            <p>Hello {user.username},</p>
            <p>We received a request to reset your Boostivon password. Click the button below to reset it now.</p>
            <p style="text-align:center;margin:30px 0">
                <a href="{reset_url}" style="display:inline-block;padding:14px 24px;background:#0b76c2;color:#fff;text-decoration:none;border-radius:6px">Reset Password</a>
            </p>
            <p>If the button above does not work, copy and paste this link into your browser:</p>
            <p><a href="{reset_url}">{reset_url}</a></p>
            <p>This link expires in 30 minutes and can only be used once.</p>
            <p>If you did not request a password reset, please ignore this email.</p>
            <hr>
            <p style="color:#666;font-size:0.9em">Boostivon • www.boostivon.com.ng</p>
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

def buy_product():
    ...
def convert_price_to_naira(price_in_dollars):
    url = f"https://api.fastforex.io/convert?from=USD&to=NGN&amount={price_in_dollars}&api_key={settings.CURRENCY_CONVERSION_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        exchange_rate = data['result']['NGN']
        return exchange_rate
    except Exception as e:
        print(f"Error converting price: {str(e)}")
        return 1  # Fallback to 1 if conversion fails
    
def price(x):
    if x < 10000:
        x += x
    else:
        y = x * 50/100
        x += y
    
    return x