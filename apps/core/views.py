import pyotp
from django.db import transaction
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from drf_spectacular.utils import OpenApiResponse, extend_schema, OpenApiExample
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenBlacklistSerializer, TokenRefreshSerializer, \
    TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenBlacklistView, TokenRefreshView

from apps.common.permissions import IsAuthenticatedUser
from apps.common.responses import CustomResponse
from apps.core.emails import send_email_verification, send_otp_email
from apps.core.models import NormalProfile, CompanyProfile
from apps.core.selectors import *
from apps.core.serializers import *
from apps.core.tokens import account_activation_token
from utilities.encryption import decrypt_token_to_profile, encrypt_profile_to_token

User = get_user_model()

# Create your views here.


"""
REGISTRATION
"""


class NormalRegistrationView(APIView):
    serializer_class = NormalRegisterSerializer

    @extend_schema(
        summary="User Registration",
        description=(
                """
                This endpoint allows a user to register as a normal user on the platform
                
                This also returns to you the secret for the email which should be used for verification
                """
        ),
        tags=['Registration'],
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                description="Registration successful, check your email for verification.",
                response=NormalProfileSerializer,
            ),
            status.HTTP_409_CONFLICT: OpenApiResponse(
                response={"application/json"},
                description="Account already exists and has an company profile",
                examples=[
                    OpenApiExample(
                        name="Agent Conflict response",
                        value={
                            "status": "failure",
                            "message": "Account already exists and has an company profile",
                            "code": "already_exists"
                        }
                    ),
                    OpenApiExample(
                        name="Normal Conflict response",
                        value={
                            "status": "failure",
                            "message": "Account already exists and has a normal profile",
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

        data = serializer.validated_data
        email = data.get('email')
        full_name = data.pop('last_name') + " " + data.pop('first_name')

        # Check if user with the same exists and which profile they have
        get_existing_user(email=email)

        try:
            user = User.objects.create_user(full_name=full_name, **serializer.validated_data)
            user_profile = NormalProfile.objects.create(user=user)
        except Exception as e:
            raise RequestError(err_code=ErrorCode.OTHER_ERROR, err_msg=str(e),
                               status_code=status.HTTP_400_BAD_REQUEST)

        data = {
            "user_data": NormalProfileSerializer(user_profile).data
        }

        send_email_verification(request=request, recipient=user, template='email_verification.html')
        return CustomResponse.success(message="Registration successful, check your email for verification.",
                                      status_code=status.HTTP_201_CREATED, data=data)


class CompanyRegistrationView(APIView):
    serializer_class = CompanyRegisterSerializer

    @extend_schema(
        summary="Agent Registration",
        description=(
                """
                This endpoint allows a user to register as an agent on the platform

                This also returns to you the secret for the email which should be used for verification
                """
        ),
        tags=['Registration'],
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                description="Registration successful, check your email for verification.",
                response=CompanyProfileSerializer,
            ),
            status.HTTP_409_CONFLICT: OpenApiResponse(
                response={"application/json"},
                description="Account already exists and has an company profile",
                examples=[
                    OpenApiExample(
                        name="Agent Conflict response",
                        value={
                            "status": "failure",
                            "message": "Account already exists and has an company profile",
                            "code": "already_exists"
                        }
                    ),
                    OpenApiExample(
                        name="Normal Conflict response",
                        value={
                            "status": "failure",
                            "message": "Account already exists and has a normal profile",
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

        data = serializer.validated_data
        email = data.get('email')
        company_name = data.pop('company_name')
        licence_number = data.pop('licence_number')

        # Check if user with the same exists and which profile they have
        get_existing_user(email=email)

        try:
            user = User.objects.create_user(**serializer.validated_data, is_agent=True)
            user_profile = CompanyProfile.objects.create(user=user, company_name=company_name,
                                                         license_number=licence_number)
        except Exception as e:
            raise RequestError(err_code=ErrorCode.OTHER_ERROR, err_msg=str(e),
                               status_code=status.HTTP_400_BAD_REQUEST)

        data = {
            "user_data": CompanyProfileSerializer(user_profile).data
        }

        send_email_verification(request=request, recipient=user, template='email_verification.html')
        return CustomResponse.success(message="Registration successful, check your email for verification.",
                                      status_code=status.HTTP_201_CREATED, data=data)


"""
AUTHENTICATION AND VERIFICATION OPTIONS 
"""


class VerifyEmailView(APIView):

    @extend_schema(
        summary="Email verification",
        description="""
        This endpoint allows a registered user to verify their email address with the email link.
        Pass in the uidb64 and token generated or sent to the email address 
        """,
        tags=['Email Verification'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"application/json"},
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
                            "status": "success",
                            "message": "Email already verified",
                            "code": "verified_user"
                        }
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"application/json"},
                description="Not found",
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
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response={"application/json"},
                description="The link is invalid",
                examples=[
                    OpenApiExample(
                        name="Invalid link response",
                        value={
                            "status": "failure",
                            "message": "The link is invalid",
                            "code": "other_error"
                        }
                    )
                ]
            )
        }
    )
    def get(self, request, *args, **kwargs):
        uidb64 = kwargs.get('uidb64')
        token = kwargs.get('token')

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=uid)
        except(TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user.email_verified:
            raise RequestError(err_code=ErrorCode.VERIFIED_USER, err_msg="Email verified already",
                               status_code=status.HTTP_200_OK)

        if user and account_activation_token.check_token(user, token):
            # OTP verification successful
            user.email_verified = True
            user.save()
        else:
            raise RequestError(err_code=ErrorCode.OTHER_ERROR, err_msg='The link is invalid',
                               status_code=status.HTTP_400_BAD_REQUEST)

        return CustomResponse.success(message="Email verification successful.")


class ResendEmailVerificationLinkView(APIView):
    serializer_class = ResendEmailVerificationLinkSerializer

    @extend_schema(
        summary="Send / resend email verification link",
        description="""
        This endpoint allows a registered user to send or resend email verification link to their registered email address.
        The request should include the following data:

        - `email_address`: The user's email address.
        """,
        tags=['Email Verification'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"application/json"},
                description="Verification link sent successfully. Please check your mail.",
                examples=[
                    OpenApiExample(
                        name="Verification successful response",
                        value={
                            "status": "success",
                            "message": "Verification link sent successfully. Please check your mail."
                        }
                    ),
                    OpenApiExample(
                        name="Already verified response",
                        value={
                            "status": "success",
                            "message": "Email already verified",
                            "error_code": "already_verified"
                        }
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"application/json"},
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

        send_email_verification(request=request, recipient=user, template='email_verification.html')

        return CustomResponse.success("Verification link sent successfully. Please check your mail")


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
                        name="Agent response",
                        value={
                            "status": "success",
                            "message": "Logged in successfully",
                            "data": {
                                "tokens": {
                                    "access": "token",
                                    "refresh": "refresh token",
                                },
                                "profile_data": {
                                    "user_id": "59af4ef1-8e58-47cf-9f1a-e7bae786b883",
                                    "id": "542ee57a-7a5e-4332-a9a7-4de9a775e570",
                                    "full_name": "John Doe",
                                    "company_name": "Doecomp",
                                    "email": "ayflix0@gmail.com",
                                    "image": "",
                                    "background_image": "",
                                    "phone_number": "+2348099691398",
                                    "license_number": "121234575",
                                    "location": "",
                                    "website": ""
                                }
                            }
                        }
                    ),
                    OpenApiExample(
                        name="Normal response",
                        value={
                            "status": "success",
                            "message": "Logged in successfully",
                            "data": {
                                "tokens": {
                                    "access": "token",
                                    "refresh": "refresh token",
                                },
                                "profile_data": {
                                    "user_id": "59af4ef1-8e58-47cf-9f1a-e7bae786b883",
                                    "id": "542ee57a-7a5e-4332-a9a7-4de9a775e570",
                                    "full_name": "Doe",
                                    "email": "a@gmail.com",
                                    "phone_number": "+2348099691398",
                                    "image": "",
                                    "date_of_birth": "2024-10-05"
                                }
                            }
                        }
                    )
                ]
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response={'application/json'},
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
                response={'application/json'},
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

        email = serializer.validated_data.get('email')
        password = serializer.validated_data["password"]
        is_agent = serializer.validated_data["is_agent"]

        # authenticating user
        user = authenticate_user(email, password)

        # checking if the email is verified
        check_email_verification(user)

        user_profile = get_user_profile(user, is_agent)
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
                response={'application/json'},
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
                response={'application/json'},
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
        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
        except TokenError:
            raise RequestError(err_code=ErrorCode.INVALID_ENTRY, err_msg="Error refreshing token",
                               status_code=status.HTTP_400_BAD_REQUEST)

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
        This will also return to you an otp secret that you can use to reset your password.
        """,
        tags=['Password Change'],
        responses={
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={'application/json'},
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
                response={'application/json'},
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

        # Generate OTP secret for the user
        otp_secret = pyotp.random_base32()

        send_otp_email(otp_secret=otp_secret, recipient=user, template="forgot_password.html")

        data = {
            "otp_secret": otp_secret
        }
        return CustomResponse.success(message="Password code sent successfully", data=data)


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
                response={'application/json'},
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
                response={'application/json'},
                description="OTP Error",
                examples=[
                    OpenApiExample(
                        name="Invalid OTP response",
                        value={
                            "status": "failure",
                            "message": "Invalid OTP",
                            "code": "incorrect_otp"
                        }
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={'application/json'},
                description="Not found",
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
    def post(self, request, *args, **kwargs):
        otp_secret = kwargs.get('otp_secret')

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get("email")
        code = serializer.validated_data.get("otp")

        user = get_user(email=email)

        otp_verification(otp_secret=otp_secret, code=code)

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
                response={'application/json'},
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
                response={'application/json'},
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
NORMAL PROFILE
"""


class RetrieveUpdateProfileView(APIView):
    permission_classes = (IsAuthenticatedUser,)
    serializer_class = NormalProfileSerializer

    @extend_schema(
        summary="Retrieve user profile",
        description="""
        This endpoint allows a user to retrieve his/her normal profile. 
        Note: Also use this endpoint for the admin section too for the user section
        """,
        tags=['Normal Profile'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Fetched successfully",
                response={'application/json'},
                examples=[
                    OpenApiExample(
                        name="Normal profile response",
                        value={
                            "status": "success",
                            "message": "Retrieved profile successfully",
                            "data": {
                                "user_id": "7ce89870-e34c-4c39-85ea-275693a997e8",
                                "id": "b1996656-f69d-4ae9-8bef-63e09c8de681",
                                "full_name": "Jop Doe",
                                "email": "admin@gmail.com",
                                "phone_number": "+2347627322",
                                "date_of_birth": "2020-12-12",
                                "image": "https://google.com"
                            }
                        }
                    )
                ]
            )
        }
    )
    def get(self, request):
        user = request.user
        try:
            user_profile = NormalProfile.objects.select_related('user').get(user=user)
        except NormalProfile.DoesNotExist:
            raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="No profile found for this user",
                               status_code=status.HTTP_404_NOT_FOUND)

        serialized_data = self.serializer_class(user_profile, context={"request": request}).data
        return CustomResponse.success(message="Retrieved profile successfully", data=serialized_data)

    @extend_schema(
        summary="Update user profile",
        description="""
        This endpoint allows a user to update his/her user profile.
        """,
        tags=['Normal Profile'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Updated profile successfully",
                response={'application/json'},
                examples=[
                    OpenApiExample(
                        name="Normal profile response",
                        value={
                            "status": "success",
                            "message": "Updated profile successfully",
                            "data": {
                                "user_id": "0cf8dd0c-29ca-4b95-a9c7-529993d3891f",
                                "id": "0a445bca-a6d0-427e-9f36-da780132d0db",
                                "full_name": "John Doe",
                                "company_name": "Corpoann",
                                "email": "ayflix@gmail.com",
                                "image": "url",
                                "background_image": "url",
                                "phone_number": "+23345662323",
                                "license_number": "2323232424",
                                "location": "Canadsa",
                                "website": "htttps://google.com"
                            }
                        }
                    )
                ]
            )
        }
    )
    @transaction.atomic()
    def patch(self, request):
        user = request.user
        user_profile = NormalProfile.objects.select_related('user').get(user=user)
        update_profile = self.serializer_class(user_profile, data=self.request.data, partial=True, )

        update_profile.is_valid(raise_exception=True)
        updated = self.serializer_class(update_profile.save()).data
        return CustomResponse.success(message="Updated profile successfully", data=updated,
                                      status_code=status.HTTP_202_ACCEPTED)
