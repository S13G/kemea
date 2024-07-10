import pyotp
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.core.tokens import account_activation_token
from utilities.emails import send_email

User = get_user_model()


def send_email_verification(request: HttpRequest, recipient: User, template: str) -> None:
    current_site = get_current_site(request)

    # Determine email address based on the type of recipient
    if isinstance(recipient, User):
        email_address = recipient.email
    else:
        email_address = recipient

    subject = 'Email Verification'
    recipients = [email_address]
    context = {'email': email_address, 'domain': current_site.domain,
               'uid': urlsafe_base64_encode(force_bytes(recipient.pk)),
               'protocol': 'https' if request.is_secure() else 'http',
               'token': account_activation_token.make_token(recipient), }

    message = render_to_string(template, context)

    # Send the email
    send_email(subject, recipients, message=message, template=template, context=context)


def decode_otp_from_secret(otp_secret: str) -> str:
    # Generate the OTP using the secret
    # Otp lasts for 5 minutes
    totp = pyotp.TOTP(s=otp_secret, interval=300, digits=4)  # Limit the generated otp to 4 digits

    otp = totp.now()
    return otp


def send_otp_email(otp_secret: str, recipient: str or User, template=None) -> None:
    # Generate the OTP using the secret
    otp = decode_otp_from_secret(otp_secret=otp_secret)

    # Determine email address based on the type of recipient
    if isinstance(recipient, User):
        email_address = recipient.email
    else:
        email_address = recipient

    subject = 'One-Time Password (OTP) Verification'
    recipients = [email_address]
    context = {'email': email_address, 'otp': otp}
    message = render_to_string(template, context)

    # Send the email
    send_email(subject, recipients, message=message, template=template, context=context)
