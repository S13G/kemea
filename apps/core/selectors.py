from django.contrib.auth import get_user_model, authenticate
from rest_framework import status

from apps.common.errors import ErrorCode
from apps.common.exceptions import RequestError
from apps.core.emails import decode_otp_from_secret
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
        return User.objects.get(email=email)
    except User.DoesNotExist:
        raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="User with this email not found",
                           status_code=status.HTTP_404_NOT_FOUND)


def otp_verification(otp_secret: str, code: str):
    otp = decode_otp_from_secret(otp_secret=otp_secret)

    if otp != code:
        raise RequestError(err_code=ErrorCode.INCORRECT_OTP, err_msg="Invalid OTP",
                           status_code=status.HTTP_400_BAD_REQUEST)
