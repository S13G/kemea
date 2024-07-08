from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample
from rest_framework import status
from rest_framework.views import APIView

from apps.common.responses import CustomResponse
from apps.misc.models import Policy


# Create your views here.


class RetrievePoliciesView(APIView):

    @extend_schema(
        summary="Retrieve Policies",
        description=
        """
        This endpoint retrieves the policies or terms and conditions based on the language passed as a parameter to the endpoint
        e.g. fr, en, es, etc.
        """,
        parameters=[
            OpenApiParameter(name='lang', description='Language of the policy', required=True, type=OpenApiTypes.STR)
        ],
        tags=['Policy'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={'application/json'},
                description='Retrieved successfully',
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={}
                    )
                ]
            )
        }
    )
    def get(self, request, *args, **kwargs):
        lang = request.query_params.get('lang', 'en')

        try:
            policy = Policy.objects.get(language=lang)
        except Policy.DoesNotExist:
            try:
                policy = Policy.objects.get(language='en')
            except Policy.DoesNotExist:
                return CustomResponse.success(message='Retrieved successfully', data={})

        data = {
            'title': policy.title,
            'language': policy.language,
            'content': policy.content
        }
        return CustomResponse.success(message='Retrieved successfully', data=data)
