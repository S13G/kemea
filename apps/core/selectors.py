from datetime import timedelta

from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from rest_framework import status

from apps.common.errors import ErrorCode
from apps.common.exceptions import RequestError
from apps.common.responses import CustomResponse
from apps.core.models import OTPSecret
from apps.core.serializers import CompanyProfileSerializer, NormalProfileSerializer

User = get_user_model()


def authenticate_user(email, password):
    user = authenticate(email=email, password=password)
    if user is None:
        raise RequestError(err_code=ErrorCode.INVALID_CREDENTIALS, err_msg="Invalid credentials",
                           status_code=status.HTTP_401_UNAUTHORIZED)
    return user


def check_email_verification(user):
    if not user.email_verified:
        raise RequestError(err_code=ErrorCode.UNVERIFIED_USER, err_msg="Verify your email first",
                           status_code=status.HTTP_400_BAD_REQUEST)


def get_user_profile(user, is_agent):
    if is_agent:
        return CompanyProfileSerializer(user.company_profile)
    else:
        # Assuming you have a different serializer for non-agent users
        return NormalProfileSerializer(user.profile)


def generate_response(user, user_profile):
    response_data = {"tokens": user.tokens(), "profile_data": user_profile.data}
    return CustomResponse.success(message="Logged in successfully", data=response_data)


def get_existing_user(email):
    # Check if a user with the specified email exists
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return None  # User does not exist

    # User exists; handle different scenarios based on user profile
    if user.is_agent:
        error_msg = "Account already exists and has an company profile"
    else:
        error_msg = "Account already exists and has a normal profile"

    # Raise a RequestError with appropriate error code and message
    raise RequestError(
        err_code=ErrorCode.ALREADY_EXISTS,
        err_msg=error_msg,
        status_code=status.HTTP_409_CONFLICT
    )


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
