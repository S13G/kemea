from django.db import transaction
from drf_spectacular.utils import OpenApiResponse, extend_schema, OpenApiExample
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenBlacklistSerializer, TokenRefreshSerializer, \
    TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenBlacklistView, TokenRefreshView

from apps.common.errors import ErrorCode
from apps.common.exceptions import RequestError
from apps.common.responses import CustomResponse
from apps.core.emails import send_otp_email
from apps.core.models import Profile, Referral
from apps.core.selectors import authenticate, get_existing_user, get_user, validate_otp_secret_code, get_otp_secret, \
    verify_otp, verify_otp_expiration, get_profile, get_referral_code_owner, award_referral_tokens
from apps.core.serializers import *
from utilities.encryption import decrypt_token_to_profile, encrypt_profile_to_token

User = get_user_model()

# Create your views here.


"""
REGISTRATION
"""


class RegistrationView(APIView):
    serializer_class = RegisterSerializer

    @extend_schema(
        summary="Registration",
        description=(
                """
                This endpoint allows a user to register on the wejpal application
                """
        ),
        tags=['Registration'],
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                description="Registration successful, check your email for verification.",
                response=ProfileSerializer,
            ),
            status.HTTP_409_CONFLICT: OpenApiResponse(
                response={"status": "failure", "message": "Account already exists",
                          "code": "already_exists"},
                description="Account already exists",
                examples=[
                    OpenApiExample(
                        name="Conflict response",
                        value={
                            "status": "failure",
                            "message": "Account already exists",
                            "code": "already_exists"
                        }
                    )
                ]
            ),
        }
    )
    @transaction.atomic()
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get('email')
        username = serializer.validated_data.get('username')
        referral_code = serializer.validated_data.pop('referral')

        # Check if user with the same username or email exists
        get_existing_user(email=email, username=username)

        # Check if referral code is entered and checks if the owner of the referral code exists
        if len(referral_code) > 0:
            if not User.objects.filter(referral_code=referral_code).exists():
                raise RequestError(err_code=ErrorCode.INVALID_REFERRAL_CODE, err_msg="Invalid referral code",
                                   status_code=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.create_user(**serializer.validated_data)
            user_profile = Profile.objects.create(user=user)
        except Exception as e:
            raise RequestError(err_code=ErrorCode.OTHER_ERROR, err_msg=str(e),
                               status_code=status.HTTP_400_BAD_REQUEST)

        if len(referral_code) > 0:
            # awards the referral with 1000 tokens and the new user with 500 tokens
            referral_code_owner = get_referral_code_owner(referral_code)
            award_referral_tokens(referral_code_owner, user)

        data = ProfileSerializer(user_profile).data

        send_otp_email(user=user, template='email_verification.html')
        return CustomResponse.success(message="Registration successful, check your email for verification.",
                                      status_code=status.HTTP_201_CREATED, data=data)


"""
AUTHENTICATION AND VERIFICATION OPTIONS 
"""


class VerifyEmailView(APIView):
    serializer_class = VerifyEmailSerializer

    @extend_schema(
        summary="Email verification",
        description="""
        This endpoint allows a registered user to verify their email address with an OTP.
        The request should include the following data:

        - `email_address`: The user's email address.
        - `otp`: The otp sent to the user's email address.
        """,
        tags=['Email Verification'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"status": "success", "message": "Email verification successful or already verified."},
                description="Email verification successful or already verified.",
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "status": "success",
                            "message": "Email verification successful"
                        }
                    ),
                    OpenApiExample(
                        name="Already verified response",
                        value={
                            "status": "error",
                            "message": "Email already verified",
                            "code": "verified_user"
                        }
                    )
                ]
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response={"status": "failure", "message": "Invalid OTP", "code": "incorrect_otp"},
                description="OTP Error",
                examples=[
                    OpenApiExample(
                        name="Invalid OTP response",
                        value={
                            "status": "failure",
                            "message": "Invalid OTP",
                            "code": "incorrect_otp"
                        }
                    ),
                    OpenApiExample(
                        name="Expired OTP response",
                        value={
                            "status": "failure",
                            "message": "OTP has expired",
                            "code": "expired_otp"
                        }
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"status": "failure", "message": "Not found", "code": "non_existent"},
                description="Not found",
                examples=[
                    OpenApiExample(
                        name="Email not found response",
                        value={
                            "status": "failure",
                            "message": "User with this email not found",
                            "code": "non_existent"
                        }
                    ),
                    OpenApiExample(
                        name="No otp found response",
                        value={
                            "status": "failure",
                            "message": "No OTP found for this account",
                            "code": "non_existent"
                        }
                    ),
                    OpenApiExample(
                        name="No OTP secret found response",
                        value={
                            "status": "failure",
                            "message": "No OTP secret found for this account",
                            "code": "non_existent"
                        }
                    )
                ]
            )
        }
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')
        code = request.data.get('otp')

        user = get_user(email=email)

        if user.email_verified:
            raise RequestError(err_code=ErrorCode.VERIFIED_USER, err_msg="Email verified already",
                               status_code=status.HTTP_200_OK)

        validate_otp_secret_code(user=user, code=code)

        # OTP verification successful
        user.email_verified = True
        user.save()
        user.otp_secret.delete()

        return CustomResponse.success(message="Email verification successful.")


class ResendEmailVerificationCodeView(APIView):
    serializer_class = ResendEmailVerificationCodeSerializer

    @extend_schema(
        summary="Send / resend email verification code",
        description="""
        This endpoint allows a registered user to send or resend email verification code to their registered email address.
        The request should include the following data:

        - `email_address`: The user's email address.
        """,
        tags=['Email Verification'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"status": "success",
                          "message": "Verification code sent successfully. Please check your mail."},
                description="Verification code sent successfully. Please check your mail.",
                examples=[
                    OpenApiExample(
                        name="Verification successful response",
                        value={
                            "status": "success",
                            "message": "Verification code sent successfully. Please check your mail."
                        }
                    ),
                    OpenApiExample(
                        name="Already verified response",
                        value={
                            "status": "error",
                            "message": "Email already verified",
                            "error_code": "already_verified"
                        }
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"status": "failure", "message": "User with this email not found", "code": "non_existent"},
                description="User with this email not found",
                examples=[
                    OpenApiExample(
                        name="Email not found response",
                        value={
                            "status": "failure",
                            "message": "User with this email not found",
                            "code": "non_existent"
                        }
                    )
                ]
            )
        }
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')

        user = get_user(email=email)

        if user.email_verified:
            raise RequestError(err_code=ErrorCode.VERIFIED_USER, err_msg="Email already verified",
                               status_code=status.HTTP_200_OK)

        send_otp_email(user, template="email_verification.html")
        return CustomResponse.success("Verification code sent successfully. Please check your mail")


class SendNewEmailVerificationCodeView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = SendNewEmailVerificationCodeSerializer

    @extend_schema(
        summary="Send email change verification code",
        description="""
        This endpoint allows an authenticated user to send a verification code to new email they want to change to.
        The request should include the following data:

        - `email_address`: The user's new email address.
        """,
        tags=['Email Change'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"status": "success",
                          "message": "Verification code sent successfully. Please check your new email."},
                description="Verification code sent successfully. Please check your new email.",
                examples=[
                    OpenApiExample(
                        name="Verification successful response",
                        value={
                            "status": "success",
                            "message": "Verification code sent successfully. Please check your new email."
                        }
                    )
                ]
            ),
            status.HTTP_409_CONFLICT: OpenApiResponse(
                response={"status": "failure", "message": "Account with this email already exists",
                          "code": "already_exists"},
                description="Account with this email already exists",
                examples=[
                    OpenApiExample(
                        name="Conflict response",
                        value={
                            "status": "failure",
                            "message": "Account with this email already exists",
                            "code": "already_exists"
                        }
                    )
                ]
            )
        }
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')

        # Check if user with the same username or email exists
        get_existing_user(email=email)

        # send email if the email is new
        send_otp_email(request.user, template="email_change.html")
        return CustomResponse.success("Verification code sent successfully. Please check your mail")


class ChangeEmailView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ChangeEmailSerializer

    @extend_schema(
        summary="Change account email address",
        description="""
        This endpoint allows an authenticated user to change their account's email address and user can change after 10 days.
        The request should include the following data:

        - `email_address`: The user's new email address.
        - `otp`: The code sent
        """,
        tags=['Email Change'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"status": "success", "message": "Email changed successfully."},
                description="Email changed successfully.",
                examples=[
                    OpenApiExample(
                        name="Successful response",
                        value={
                            "status": "success",
                            "message": "Email changed successfully."
                        }
                    )
                ]
            ),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                response={"status": "failure", "message": "You can't use your previous email", "code": "old_email"},
                description="You can't use your previous email",
                examples=[
                    OpenApiExample(
                        name="Old email response",
                        value={
                            "status": "failure",
                            "message": "You can't use your previous email",
                            "code": "old_email"
                        }
                    )
                ]
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response={"status": "failure", "message": "Invalid OTP", "code": "incorrect_otp"},
                description="OTP Error",
                examples=[
                    OpenApiExample(
                        name="Invalid OTP response",
                        value={
                            "status": "failure",
                            "message": "Invalid OTP",
                            "code": "incorrect_otp"
                        }
                    ),
                    OpenApiExample(
                        name="Expired OTP response",
                        value={
                            "status": "failure",
                            "message": "OTP has expired",
                            "code": "expired_otp"
                        }
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"status": "failure", "message": "Not found", "code": "non_existent"},
                description="Not OTP found",
                examples=[
                    OpenApiExample(
                        name="No otp found response",
                        value={
                            "status": "failure",
                            "message": "No OTP found for this account",
                            "code": "non_existent"
                        }
                    ),

                ]
            )
        }
    )
    @transaction.atomic()
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_email = serializer.validated_data.get('email')
        otp = serializer.validated_data.get('otp')
        user = request.user

        otp_secret = get_otp_secret(user=user)

        if user.email == new_email:
            raise RequestError(err_code=ErrorCode.OLD_EMAIL, err_msg="You can't use your previous email",
                               status_code=status.HTTP_403_FORBIDDEN)

        # Check if the OTP secret has expired (10 minutes interval)
        verify_otp_expiration(otp_secret=otp_secret)

        # Verify the OTP
        verify_otp(otp_secret=otp_secret, code=otp)

        user.email = new_email
        user.save()
        user.otp_secret.delete()

        return CustomResponse.success(message="Email changed successfully.")


class LoginView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        summary="Login",
        description="""
        This endpoint authenticates a registered and verified user and provides the necessary authentication tokens.
        """,
        request=LoginSerializer,
        tags=['Login'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={'application/json'},
                description="Logged in successfully",
                examples=[
                    OpenApiExample(
                        name="Successful response",
                        value={
                            "status": "success",
                            "message": "Logged in successfully",
                            "data": {
                                "tokens": {
                                    "access": "token",
                                    "refresh": "refresh token",
                                },
                                "profile_data": {
                                    "user_id": "9022f682-201e-4391-9133-d5cfca96cebf",
                                    "id": "2775f14e-802a-43bd-b0a3-a9635207851a",
                                    "full_name": "Pala",
                                    "username": "doe",
                                    "date_of_birth": "",
                                    "email": "admin@gmail.com",
                                    "avatar": "",
                                    "referral_code": "15KHZHYN7P",
                                    "followers": 0,
                                    "tokens": 100000
                                }
                            }
                        }
                    )
                ]
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response={"status": "failure", "message": "Verify your email first", "code": "invalid_credentials"},
                description="Invalid credentials",
                examples=[
                    OpenApiExample(
                        name="Unverified email response",
                        value={
                            "status": "failure",
                            "message": "Verify your email first",
                            "code": "unverified_email"
                        }
                    )
                ]
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                response={"status": "failure", "message": "Invalid credentials", "code": "invalid_credentials"},
                description="Invalid credentials",
                examples=[
                    OpenApiExample(
                        name="Invalid credentials",
                        value={
                            "status": "failure",
                            "message": "Invalid credentials",
                            "code": "invalid_credentials"
                        }
                    ),
                ]
            )
        }
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email_or_username = serializer.validated_data.get('email_or_username')
        password = serializer.validated_data["password"]
        # authenticating user(custom authentication)
        user = authenticate(email_or_username=email_or_username, password=password)

        if user is None:
            raise RequestError(err_code=ErrorCode.INVALID_CREDENTIALS, err_msg="Invalid credentials",
                               status_code=status.HTTP_401_UNAUTHORIZED)

        if not user.email_verified:
            raise RequestError(err_code=ErrorCode.UNVERIFIED_USER, err_msg="Verify your email first",
                               status_code=status.HTTP_400_BAD_REQUEST)

        user_profile = ProfileSerializer(user.profile)

        # tokens
        response_data = {"tokens": user.tokens(), "profile_data": user_profile.data}
        return CustomResponse.success(message="Logged in successfully", data=response_data)


class LogoutView(TokenBlacklistView):
    serializer_class = TokenBlacklistSerializer

    @extend_schema(
        summary="Logout",
        description="""
        This endpoint logs out an authenticated user by blacklisting their access token.
        The request should include the following data:

        - `refresh`: The refresh token used for authentication.
        """,
        tags=['Logout'],
        responses={
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response={"status": "failure", "message": "Token is blacklisted", "code": "invalid_entry"},
                description="Token is blacklisted",
                examples=[
                    OpenApiExample(
                        name="Blacklisted token response",
                        value={
                            "status": "failure",
                            "message": "Token is blacklisted",
                            "code": "invalid_entry"
                        }
                    )
                ]
            ),
            status.HTTP_200_OK: OpenApiResponse(
                response={"status": "success", "message": "Logged out successfully"},
                description="Logged out successfully",
                examples=[
                    OpenApiExample(
                        name="Logout successful response",
                        value={
                            "status": "success",
                            "message": "Logged out successfully"
                        }
                    )
                ]
            )
        }
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            return CustomResponse.success(message="Logged out successfully.")
        except TokenError:
            raise RequestError(err_code=ErrorCode.INVALID_ENTRY, err_msg="Token is blacklisted",
                               status_code=status.HTTP_400_BAD_REQUEST)


class RefreshView(TokenRefreshView):
    serializer_class = TokenRefreshSerializer

    @extend_schema(
        summary="Refresh token",
        description="""
        This endpoint allows a user to refresh an expired access token.
        The request should include the following data:

        - `refresh`: The refresh token.
        """,
        tags=['Token'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=TokenRefreshSerializer,
                description="Refreshed successfully",
            ),
        }

    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        access_token = serializer.validated_data['access']
        return CustomResponse.success(message="Refreshed successfully", data=access_token)


class RequestForgotPasswordCodeView(APIView):
    serializer_class = RequestNewPasswordCodeSerializer
    throttle_classes = [AnonRateThrottle]

    @extend_schema(
        summary="Request new password code for forgot password",
        description="""
        This endpoint allows a user to request a verification code to reset their password if forgotten.
        The request should include the following data:

        - `email`: The user's email address.
        """,
        tags=['Password Change'],
        responses={
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"status": "failure", "message": "Account not found", "code": "non_existent"},
                description="Account not found",
                examples=[
                    OpenApiExample(
                        name="Account not found response",
                        value={
                            "status": "failure",
                            "message": "Account not found",
                            "code": "non_existent"
                        }
                    )
                ]
            ),
            status.HTTP_200_OK: OpenApiResponse(
                response={"status": "success", "message": "Password code sent successfully"},
                description="Password code sent successfully",
                examples=[
                    OpenApiExample(
                        name="Password code sent response",
                        value={
                            "status": "success",
                            "message": "Password code sent successfully"
                        }
                    )
                ]
            )
        }

    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')

        user = get_user(email=email)

        send_otp_email(user, "forgot_password.html")
        return CustomResponse.success(message="Password code sent successfully")


class VerifyForgotPasswordCodeView(APIView):
    serializer_class = VerifyEmailSerializer
    throttle_classes = [AnonRateThrottle]

    @extend_schema(
        summary="Verify forgot password code for unauthenticated users",
        description="""
        This endpoint allows a user to verify the verification code they got to reset the password if forgotten.
        The user will be stored in the token which will be gotten to make sure it is the right user that is
        changing his/her password

        The request should include the following data:

        - `email`: The user's email
        - `otp`: The verification code sent to the user's email.
        """,
        tags=['Password Change'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"status": "success", "message": "Otp verified successfully."},
                description="Otp verified successfully.",
                examples=[
                    OpenApiExample(
                        name="Otp verified response",
                        value={
                            "status": "success",
                            "message": "Otp verified successfully",
                            "data": "<token>"
                        }
                    )
                ]
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response={"status": "failure", "message": "Invalid OTP", "code": "incorrect_otp"},
                description="OTP Error",
                examples=[
                    OpenApiExample(
                        name="Invalid OTP response",
                        value={
                            "status": "failure",
                            "message": "Invalid OTP",
                            "code": "incorrect_otp"
                        }
                    ),
                    OpenApiExample(
                        name="Expired OTP response",
                        value={
                            "status": "failure",
                            "message": "OTP has expired",
                            "code": "expired_otp"
                        }
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"status": "failure", "message": "Not found", "code": "non_existent"},
                description="Not found",
                examples=[
                    OpenApiExample(
                        name="Email not found response",
                        value={
                            "status": "failure",
                            "message": "User with this email not found",
                            "code": "non_existent"
                        }
                    ),
                    OpenApiExample(
                        name="No otp found response",
                        value={
                            "status": "failure",
                            "message": "No OTP found for this account",
                            "code": "non_existent"
                        }
                    ),
                    OpenApiExample(
                        name="No OTP secret found response",
                        value={
                            "status": "failure",
                            "message": "No OTP secret found for this account",
                            "code": "non_existent"
                        }
                    )
                ]
            )
        }
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get("email")
        code = serializer.validated_data.get("otp")

        user = get_user(email=email)

        otp_secret = get_otp_secret(user)

        # Check if the OTP secret has expired (10 minutes interval)
        verify_otp_expiration(otp_secret=otp_secret)

        # Verify the OTP
        verify_otp(otp_secret=otp_secret, code=code)

        token = encrypt_profile_to_token(user)  # Encrypt the user profile to a token.
        return CustomResponse.success(message="Otp verified successfully", data=token)


class ChangeForgottenPasswordView(APIView):
    serializer_class = ChangePasswordSerializer
    throttle_classes = [AnonRateThrottle]

    @extend_schema(
        summary="Change password for forgotten password",
        description="""
        This endpoint allows the unauthenticated user to change their password after requesting for a code.
        The request should include the following data:
        - `token`: Pass in the encrypted token you got from the previous endpoint.
        - `password`: The new password.
        - `confirm_password`: The new password again.
        """,
        tags=['Password Change'],
        responses={
            status.HTTP_202_ACCEPTED: OpenApiResponse(
                response={"status": "success", "message": "Password updated successfully."},
                description="Password updated successfully",
                examples=[
                    OpenApiExample(
                        name="Password updated response",
                        value={
                            "status": "success",
                            "message": "Password updated successfully.",
                        }
                    )
                ]
            ),
        }
    )
    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        token = self.kwargs.get('token')

        user = decrypt_token_to_profile(token)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        password = serializer.validated_data['password']
        user.set_password(password)
        user.save()

        return CustomResponse.success(message="Password updated successfully", status_code=status.HTTP_202_ACCEPTED)


class ChangePasswordView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ChangePasswordSerializer
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        summary="Change password for authenticated users",
        description="""
        This endpoint allows the authenticated user to change their password.
        The request should include the following data:

        - `password`: The new password.
        - `confirm_password`: The new password again.
        """,
        tags=['Password Change'],
        responses={
            status.HTTP_202_ACCEPTED: OpenApiResponse(
                response={"status": "success", "message": "Password updated successfully"},
                description="Password updated successfully",
                examples=[
                    OpenApiExample(
                        name="Password updated response",
                        value={
                            "status": "success",
                            "message": "Password updated successfully",
                        }
                    )
                ]
            ),
        }
    )
    @transaction.atomic()
    def post(self, request):
        user = request.user
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        password = serializer.validated_data['password']
        user.set_password(password)
        user.save()

        return CustomResponse.success(message="Password updated successfully", status_code=status.HTTP_202_ACCEPTED)


"""
PROFILE
"""


class RetrieveUpdateDeleteProfileView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ProfileSerializer

    @extend_schema(
        summary="Retrieve profile",
        description="""
        This endpoint allows a user to retrieve his/her profile.
        """,
        tags=['Profile'],
        responses={
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"status": "failure", "message": "No profile found for this user", "code": "non_existent"},
                description="No profile found for this user",
                examples=[
                    OpenApiExample(
                        name="No profile found response",
                        value={
                            "status": "failure",
                            "message": "No profile found for this user",
                            "code": "non_existent"
                        }
                    )
                ]
            ),
            status.HTTP_200_OK: OpenApiResponse(
                description="Retrieved profile successfully",
                response=ProfileSerializer
            )
        }
    )
    def get(self, request):
        user = request.user

        profile_instance = get_profile(user)

        serialized_data = self.serializer_class(profile_instance).data
        return CustomResponse.success(message="Retrieved profile successfully", data=serialized_data)

    @extend_schema(
        summary="Update profile",
        description="""
        This endpoint allows a user to update his/her profile.
        """,
        tags=['Profile'],
        responses={
            status.HTTP_202_ACCEPTED: OpenApiResponse(
                description="Updated profile successfully",
                response=ProfileSerializer
            )
        }
    )
    @transaction.atomic()
    def patch(self, request):
        user = request.user

        profile_instance = get_profile(user)

        update_profile = self.serializer_class(profile_instance, data=request.data, partial=True)
        update_profile.is_valid(raise_exception=True)
        saved_profile = update_profile.save()

        updated_data = self.serializer_class(saved_profile).data

        return CustomResponse.success(message="Updated profile successfully", data=updated_data,
                                      status_code=status.HTTP_202_ACCEPTED)


class DeactivateAccountView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        summary="Deactivate account",
        description="""
            This endpoint allows a user to deactivate his/her account.
            """,
        tags=['Profile'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"status": "success", "message": "Account deactivated successfully"},
                description="Account deactivated successfully",
                examples=[
                    OpenApiExample(
                        name="Deactivated response",
                        value={
                            "status": "success",
                            "message": "Account deactivated successfully"
                        }
                    )
                ]
            )
        }
    )
    def get(self, request):
        user = request.user
        user.is_active = False
        user.save()
        return CustomResponse.success(message="Account deactivated successfully")


class GetReferralInfoView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        summary="Referral overview",
        description="""
            This endpoint allows a user to view his/her referral statistics.
            """,
        tags=['Profile'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"status": "success", "message": "Retrieved successfully"},
                description="Retrieved successfully",
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "status": "success",
                            "message": "Retrieved successfully",
                            "data": {
                                "total_earnings": 10000,
                                "total_referrals": 10,
                                "referral_code": "A84NMSYTPDY",
                                "referral_link": "httpds......."
                            }
                        }
                    )
                ]
            )
        }
    )
    def get(self, request):
        user = request.user
        referral_object = Referral.objects.filter(user=user).first()
        total_earnings = referral_object.earnings if referral_object else 0
        total_referrals = referral_object.num_of_referrals if referral_object else 0
        referral_code = user.referral_code
        referral_link = request.build_absolute_uri() + '?ref=' + user.referral_code

        data = {
            "total_earnings": total_earnings,
            "total_referrals": total_referrals,
            "referral_code": referral_code,
            "referral_link": referral_link
        }

        return CustomResponse.success(message="Retrieved successfully", data=data)
