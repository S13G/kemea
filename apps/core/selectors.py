from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from rest_framework import status

from apps.common.errors import ErrorCode
from apps.common.exceptions import RequestError
from apps.core.models import OTPSecret, Profile, Referral

User = get_user_model()


def authenticate(email_or_username=None, password=None):
    try:
        user = User.objects.filter(Q(username__iexact=email_or_username) | Q(email__iexact=email_or_username)).get()
        if user.check_password(password) and user.is_active:
            return user
    except User.DoesNotExist:
        return None


def get_existing_user(email, username=None):
    if User.objects.filter(Q(email=email) | Q(username=username)).exists():
        raise RequestError(err_code=ErrorCode.ALREADY_EXISTS,
                           err_msg=f"Account already exists",
                           status_code=status.HTTP_409_CONFLICT)


def get_user(email):
    try:
        return User.objects.select_related('otp_secret').get(email=email)
    except User.DoesNotExist:
        raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="User with this email not found",
                           status_code=status.HTTP_404_NOT_FOUND)


def get_otp_secret(user):
    try:
        return OTPSecret.objects.get(user=user)
    except OTPSecret.DoesNotExist:
        raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="No OTP found for this account",
                           status_code=status.HTTP_404_NOT_FOUND)


def verify_otp(otp_secret, code):
    if otp_secret.code != code:
        raise RequestError(err_code=ErrorCode.INCORRECT_OTP, err_msg="Invalid OTP",
                           status_code=status.HTTP_400_BAD_REQUEST)


def verify_otp_expiration(otp_secret):
    current_time = timezone.now()
    expiration_time = otp_secret.created + timedelta(minutes=10)
    if current_time > expiration_time:
        raise RequestError(err_code=ErrorCode.EXPIRED_OTP, err_msg="OTP has expired",
                           status_code=status.HTTP_400_BAD_REQUEST)


def validate_otp_secret_code(user, code):
    try:
        otp_secret = OTPSecret.objects.get(user=user)

        # Verify the OTP
        if otp_secret.code != code:
            raise RequestError(err_code=ErrorCode.INCORRECT_OTP, err_msg="Invalid OTP",
                               status_code=status.HTTP_400_BAD_REQUEST)
    except OTPSecret.DoesNotExist:
        raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="No OTP found for this account",
                           status_code=status.HTTP_404_NOT_FOUND)


def get_profile(user):
    try:
        return Profile.objects.select_related('user').get(user=user)
    except Profile.DoesNotExist:
        raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="No profile found for this user",
                           status_code=status.HTTP_404_NOT_FOUND)


def get_referral_code_owner(referral_code):
    return User.objects.get(referral_code=referral_code)


def award_referral_tokens(referral_code_owner, new_user):
    try:
        referral = Referral.objects.get(user=referral_code_owner)
        referral.earnings += 1000
        referral.num_of_referrals += 1
        referral.save()
    except Referral.DoesNotExist:
        print('create')
        Referral.objects.create(user=referral_code_owner, earnings=1000, num_of_referrals=1)
    new_user.profile.tokens += 500
    new_user.profile.save()
