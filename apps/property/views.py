from django.db import transaction
from django.db.models import OuterRef, Subquery
from django.db.models.functions import Coalesce
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiTypes, OpenApiExample
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.errors import ErrorCode
from apps.common.exceptions import RequestError
from apps.common.permissions import IsAuthenticatedAgent
from apps.common.responses import CustomResponse
from apps.core.serializers import AgentProfileSerializer
from apps.property.choices import APPROVED
from apps.property.filters import AdFilter
from apps.property.models import Property, AdCategory, PropertyType, PropertyState, PropertyFeature, PropertyMedia, \
    FavoriteProperty
from apps.property.selectors import get_dashboard_details, terminate_property_ad, get_searched_property_ads, \
    get_property_for_user, update_property, get_agent_profile, get_favorite_properties, get_single_property
from apps.property.serializers import CreatePropertyAdSerializer, PropertyAdSerializer


# Create your views here.

class RetrieveAgentDashboardView(APIView):
    permission_classes = [IsAuthenticatedAgent]

    @extend_schema(
        summary="Agent dashboard",
        description="""
        This endpoint allows an authenticated agent to view their dashboard that contains their active property ads
        """,
        tags=['Agent Dashboard'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Successfully retrieved agent dashboard",
                response={"application/json"},
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={}
                    )
                ]
            )
        }
    )
    def get(self, request):
        full_name = request.user.full_name
        ads_data = get_dashboard_details(user=request.user)

        data = {
            "full_name": full_name,
            "num_of_property_ads": ads_data[0]['num_ads'] if ads_data else 0,
            "all_property_ads": list(ads_data)
        }
        return CustomResponse.success(message="Successfully retrieved agent dashboard", data=data)


class TerminatePropertyAdView(APIView):
    permission_classes = [IsAuthenticatedAgent]

    @extend_schema(
        summary="Terminate property ad",
        description="""
        This endpoint allows an authenticated agent to terminate an active property ad
        """,
        tags=['Agent Dashboard'],
    )
    def get(self, request, *args, **kwargs):
        property_ad_id = kwargs.get('property_id')

        terminate_property_ad(user=request.user, ad_id=property_ad_id)

        return CustomResponse.success(message="Successfully terminated property ad")


class SearchAgentDashboardView(APIView):
    permission_classes = [IsAuthenticatedAgent]

    @extend_schema(
        summary="Search agent dashboard",
        description="""
        This endpoint allows an authenticated agent to search their dashboard that contains their active property ads
        """,
        tags=['Agent Dashboard'],
    )
    def get(self, request, *args, **kwargs):
        search = request.query_params.get('q')

        get_property_ads = get_searched_property_ads(user=request.user, search=search)

        return CustomResponse.success(message="Successfully retrieved searched results", data=list(get_property_ads))


class RetrieveFilteredAdsView(APIView):
    permission_classes = [IsAuthenticatedAgent]
    filter_backends = [DjangoFilterBackend]
    filterset_class = AdFilter

    @extend_schema(
        summary="Filter property ads",
        description=(
                "This endpoint allows an authenticated normal user to filter properties."
        ),
        parameters=[
            OpenApiParameter(name="ad_category", description="Type of property ad", required=False,
                             type=OpenApiTypes.STR),
        ],
        tags=['Property'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Successfully retrieved filtered properties",
            )
        }
    )
    def get(self, request):
        queryset = Property.objects.only('id', 'name', 'property_type__name',
                                         'ad_category__name', 'ad_status')
        filtered_queryset = self.filterset_class(request.GET, queryset=queryset).qs.order_by('-created')
        total_items = filtered_queryset.count()

        data = {
            "total_items": total_items,
            "items": list(filtered_queryset)
        }
        return CustomResponse.success(message="Successfully retrieved filtered properties", data=data)


class RetrieveAdCategoriesView(APIView):
    permission_classes = [IsAuthenticatedAgent]

    @extend_schema(
        summary="Retrieve ad categories",
        description="""
        This endpoint allows an authenticated agent to retrieve all ad categories
        """,
        tags=['Agent Dashboard'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Successfully retrieved ad categories",
            )
        }
    )
    def get(self, request):
        ad_categories = AdCategory.objects.all()
        return CustomResponse.success(message="Successfully retrieved ad categories", data=list(ad_categories))


class RetrievePropertyTypeView(APIView):
    permission_classes = [IsAuthenticatedAgent]

    @extend_schema(
        summary="Retrieve property types",
        description="""
        This endpoint allows an authenticated agent to retrieve all property types
        """,
        tags=['Agent Dashboard'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Successfully retrieved property types",
            )
        }
    )
    def get(self, request):
        property_types = PropertyType.objects.all()
        return CustomResponse.success(message="Successfully retrieved property types", data=list(property_types))


class RetrievePropertyStateView(APIView):
    permission_classes = [IsAuthenticatedAgent]

    @extend_schema(
        summary="Retrieve property states",
        description="""
        This endpoint allows an authenticated agent to retrieve all property states
        """,
        tags=['Agent Dashboard'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Successfully retrieved property states",
            )
        }
    )
    def get(self, request):
        property_states = PropertyState.objects.all()
        return CustomResponse.success(message="Successfully retrieved property states", data=list(property_states))


class RetrievePropertyFeaturesView(APIView):
    permission_classes = [IsAuthenticatedAgent]

    @extend_schema(
        summary="Retrieve property features",
        description="""
        This endpoint allows an authenticated agent to retrieve all property features
        """,
        tags=['Agent Dashboard'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Successfully retrieved property features",
            )
        }
    )
    def get(self, request):
        property_features = PropertyFeature.objects.all()
        return CustomResponse.success(message="Successfully retrieved property features", data=list(property_features))


class CreatePropertyAdView(APIView):
    permission_classes = [IsAuthenticatedAgent]
    serializer_class = CreatePropertyAdSerializer

    @extend_schema(
        summary="Create property ad",
        description="""
        This endpoint allows an authenticated agent to create a new property ad
        Use this endpoint for both buy and sell
        """,
        tags=['Agent Dashboard'],
    )
    @transaction.atomic
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create property ad
        property_ad = Property.objects.create(lister=request.user, **serializer.validated_data)
        serialized_data = PropertyAdSerializer(property_ad).data
        return CustomResponse.success(message="Successfully created property ad", data=serialized_data,
                                      status_code=status.HTTP_201_CREATED)


class RetrieveUpdateDeletePropertyAdView(APIView):
    permission_classes = [IsAuthenticatedAgent]
    serializer_class = CreatePropertyAdSerializer

    @extend_schema(
        summary="Retrieve property ad",
        description="""
            This endpoint allows an authenticated agent to retrieve a property ad details
            Use this endpoint for both buy and sell
            """,
        tags=['Agent Dashboard'],
    )
    def get(self, request, *args, **kwargs):
        property_id = kwargs.get('id')
        property_ad = get_property_for_user(request.user, property_id=property_id)
        serialized_data = PropertyAdSerializer(property_ad).data
        return CustomResponse.success(message="Successfully retrieved property ad", data=serialized_data)

    @extend_schema(
        summary="Update property ad",
        description="""
        This endpoint allows an authenticated agent to update a property ad
        Use this endpoint for both buy and sell
        """,
        tags=['Agent Dashboard'],
    )
    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        property_id = kwargs.get('id')
        property_ad = get_property_for_user(request.user, property_id=property_id)

        serializer = self.serializer_class(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        # Update specific media
        media_data = data.pop('media', [])

        update_property(serialized_data=data, property_ad=property_ad, media_data=media_data)

        serialized_data = PropertyAdSerializer(property_ad).data
        return CustomResponse.success(message="Successfully updated property ad", data=serialized_data,
                                      status_code=status.HTTP_202_ACCEPTED)

    @extend_schema(
        summary="Delete property ad",
        description="""
        This endpoint allows an authenticated agent to delete a property ad
        """,
        tags=['Agent Dashboard'],
    )
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        property_id = kwargs.get('id')
        property_ad = get_property_for_user(request.user, property_id=property_id)
        property_ad.delete()
        return CustomResponse.success(message="Successfully deleted property ad",
                                      status_code=status.HTTP_204_NO_CONTENT)


class RetrieveUpdateAgentProfileView(APIView):
    permission_classes = [IsAuthenticatedAgent]
    serializer_class = AgentProfileSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = AdFilter

    @extend_schema(
        summary="Retrieve agent profile",
        description="""
        This endpoint allows an authenticated agent to retrieve their profile alongside their listed accepted properties
        """,
        tags=['Agent Profile'],
        parameters=[
            OpenApiParameter(name='property_type', description="Type of property", required=False,
                             type=OpenApiTypes.STR),
            OpenApiParameter(name='price_min', description="Minimum price", required=False, type=OpenApiTypes.FLOAT),
            OpenApiParameter(name='price_max', description="Maximum price", required=False, type=OpenApiTypes.FLOAT),
            OpenApiParameter(name='surface_build_min', description="Minimum surface price", required=False,
                             type=OpenApiTypes.FLOAT),
            OpenApiParameter(name='surface_build_max', description="Maximum surface price", required=False,
                             type=OpenApiTypes.FLOAT),
            OpenApiParameter(name='rooms', description="Number of rooms", required=False, type=OpenApiTypes.INT),
            OpenApiParameter(name='floors', description="Number of floors", required=False, type=OpenApiTypes.INT),
            OpenApiParameter(name='features', description="Features", required=False, type=OpenApiTypes.STR),
        ]
    )
    def get(self, request):
        user = request.user
        agent_profile = get_agent_profile(user=user)
        serialized_data = self.serializer_class(agent_profile).data
        queryset = Property.objects.filter(lister=user, ad_status=APPROVED)
        filtered_queryset = self.filterset_class(request.GET, queryset=queryset).qs.order_by('-created')
        total_number_of_ads = filtered_queryset.count()

        # Annotate the queryset with the URL of the first media file for each property
        annotated_queryset = filtered_queryset.annotate(
            first_media_url=Coalesce(
                Subquery(
                    PropertyMedia.objects.filter(property__id=OuterRef('id')).order_by('id').values('media')[:1]
                ),
                ''
            )
        )

        # Serialize the annotated queryset
        data = {
            "agent_info": serialized_data,
            "total_number_of_ads": total_number_of_ads,
            "ads": [
                {
                    "property": PropertyAdSerializer(each_property).data,
                    "first_media_url": each_property.first_media_url  # URL of the first media file
                }
                for each_property in annotated_queryset
            ]
        }
        return CustomResponse.success(message="Successfully retrieved agent profile", data=data)

    @extend_schema(
        summary="Update agent profile",
        description="""
        This endpoint allows an authenticated agent to update their profile
        """,
        tags=['Agent Profile'],
    )
    @transaction.atomic
    def patch(self, request):
        user = request.user
        agent_profile = get_agent_profile(user=user)
        serializer = self.serializer_class(agent_profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        serialized_data = self.serializer_class(serializer.save()).data
        return CustomResponse.success(message="Successfully updated agent profile", data=serialized_data,
                                      status_code=status.HTTP_202_ACCEPTED)


"""
REGISTERED USERS
"""


class RetrieveCreateDeleteFavoritePropertyView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PropertyAdSerializer

    @extend_schema(
        summary="Retrieve all favorite properties",
        description="""
        This endpoint allows an authenticated agent to retrieve all their favorite properties
        """,
        tags=['Favorites'],
    )
    def get(self, request):
        user = request.user
        property_ads = get_favorite_properties(user=user)
        serialized_data = PropertyAdSerializer(property_ads, many=True).data
        return CustomResponse.success(message="Successfully retrieved favorite properties", data=serialized_data)

    @extend_schema(
        summary="Add property to favorite properties",
        description="""
        This endpoint allows an authenticated user to add a property to their favorite properties
        """,
        tags=['Favorites'],
    )
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = request.user
        property_id = kwargs.get('id')
        property_ad = get_single_property(property_id=property_id)

        # Create property object
        FavoriteProperty.objects.create(property=property_ad, user=user)
        return CustomResponse.success(message="Successfully added property to favorite properties")

    @extend_schema(
        summary="Delete property from favorite properties",
        description="""
        This endpoint allows an authenticated user to delete a property from their favorite properties
        """,
        tags=['Favorites'],
    )
    def delete(self, request, *args, **kwargs):
        user = request.user
        property_id = kwargs.get('id')
        property_ad = get_single_property(property_id=property_id)

        try:
            FavoriteProperty.objects.get(property=property_ad, user=user).delete()
        except FavoriteProperty.DoesNotExist:
            raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="Property not found",
                               status_code=status.HTTP_404_NOT_FOUND)

        return CustomResponse.success(message="Successfully deleted property from favorite properties")


class RetrievePropertyAdDetailsView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CreatePropertyAdSerializer

    @extend_schema(
        summary="Retrieve property ad details",
        description="""
            This endpoint allows an authenticated user to retrieve a property ad details
            """,
        tags=['Agent Dashboard'],
    )
    def get(self, request, *args, **kwargs):
        property_id = kwargs.get('id')
        property_ad = get_single_property(property_id=property_id)

        serialized_data = PropertyAdSerializer(property_ad).data
        return CustomResponse.success(message="Successfully retrieved property ad", data=serialized_data)
