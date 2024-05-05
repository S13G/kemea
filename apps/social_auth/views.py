from drf_spectacular.utils import OpenApiResponse, extend_schema, OpenApiExample
from rest_framework import status
from rest_framework.generics import GenericAPIView

from apps.common.errors import ErrorCode
from apps.common.exceptions import RequestError
from apps.common.responses import CustomResponse
from apps.social_auth.serializers import GoogleSocialAuthSerializer


class GoogleSocialAuthView(GenericAPIView):
    serializer_class = GoogleSocialAuthSerializer

    @extend_schema(
        summary="Google Authentication Endpoint for registering and logging in",
        description=(
                """
                This endpoint allows users to authenticate through Google and automatically creates a profile for them if it doesn't exist.
                """
        ),
        request=GoogleSocialAuthSerializer,
        tags=['Social Authentication'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"application/json"},
                description="Success",
                examples=[
                    OpenApiExample(
                        name="Success",
                        value={
                            "status": "success",
                            "message": "Successfully authenticated",
                            "data": {
                                "tokens": {
                                    "access": "<access-token>",
                                    "refresh": "<refresh-token>"
                                },
                                "data": {
                                    "user_id": "1ef90d88-5d53-4120-b1b3-0f6066a08994",
                                    "id": "a8e4f007-ad35-435e-b43c-6e37b35f92f3",
                                    "full_name": "John Doe",
                                    "username": "john",
                                    "date_of_birth": "",
                                    "email": "johndoe@gmail.com",
                                    "avatar": "",
                                    "referral_code": "KZYLH731OI",
                                    "followers": 0
                                }
                            }
                        }
                    )
                ]
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(
                response={"application/json"},
                description="Server Error",
                examples=[
                    OpenApiExample(
                        name="Error",
                        value={
                            "status": "failure",
                            "message": "Unable to retrieve user data. Please try again later.",
                            "code": "server_error"
                        }
                    ),
                ]
            )
        }
    )
    def post(self, request):
        """
        Handles POST requests with "auth token" to get user information from Google.
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        auth_token = serializer.validated_data['id_token']

        data = auth_token.get('profile_data')

        if not data:
            raise RequestError(err_code=ErrorCode.SERVER_ERROR,
                               err_msg="Unable to retrieve user data. Please try again later.",
                               status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        tokens = auth_token.get('tokens', None)

        return CustomResponse.success(message="Successfully authenticated", data={"tokens": tokens, "data": data},
                                      status_code=status.HTTP_200_OK)
