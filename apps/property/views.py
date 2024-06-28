from django.db import transaction, IntegrityError
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiTypes, OpenApiExample
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.errors import ErrorCode
from apps.common.exceptions import RequestError
from apps.common.permissions import IsAuthenticatedAgent
from apps.common.responses import CustomResponse
from apps.core.serializers import CompanyProfileSerializer
from apps.property.choices import APPROVED
from apps.property.filters import AdFilter, PropertyAdFilter, PropertyAdListingFilter
from apps.property.models import Property, AdCategory, PropertyType, PropertyState, PropertyFeature, FavoriteProperty, \
    PromoteAdRequest, ContactCompany
from apps.property.selectors import get_dashboard_details, terminate_property_ad, get_searched_property_ads, \
    get_property_for_user, get_company_profile, get_favorite_properties, get_single_property, \
    handle_property_creation, update_property, create_company_agent, get_company_agent, \
    handle_company_availability_creation, get_company_availability, handle_company_availability_update, \
    get_searched_property_ads_by_user
from apps.property.serializers import CreatePropertyAdSerializer, PropertyAdSerializer, FavoritePropertySerializer, \
    RegisterCompanyAgentSerializer, PromoteAdSerializer, MultipleAvailabilitySerializer, CompanyAvailabilitySerializer, \
    PropertyAdMiniSerializer, ContactAgentSerializer

# Create your views here.


"""
AGENT DASHBOARD
"""


class RetrieveCompanyDashboardView(APIView):
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
                        value={
                            "status": "success",
                            "message": "Successfully retrieved agent dashboard",
                            "data": {
                                "full_name": "Sieg Domain",
                                "num_of_property_ads": 1,
                                "all_property_ads": [
                                    {
                                        "id": "691f0273-4c27-40ad-a809-3d7d0fb968d1",
                                        "name": "Property 10",
                                        "property_type__name": "Apartment",
                                        "ad_category__name": "Buy",
                                        "ad_status": "PENDING"
                                    }
                                ]
                            }
                        }
                    )
                ]
            )
        }
    )
    def get(self, request):
        full_name = request.user.full_name
        ads_data = get_dashboard_details(user=request.user)
        num_of_property_ads = len(ads_data) if ads_data else 0

        data = {
            "full_name": full_name,
            "num_of_property_ads": num_of_property_ads,
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
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={'application/json'},
                description="Successfully terminated property ad",
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "status": "success",
                            "message": "Successfully terminated property ad"
                        }
                    )
                ]
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response={'application/json'},
                description="Ad already terminated",
                examples=[
                    OpenApiExample(
                        name="Bad request",
                        value={
                            "status": "failure",
                            "message": "Ad already terminated",
                            "code": "not_allowed"
                        }
                    )
                ]
            )
        }
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
        parameters=[
            OpenApiParameter(name="search", description="Search query", required=False, type=OpenApiTypes.STR),
        ],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={'application/json'},
                description="Successfully retrieved search results",
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "status": "success",
                            "message": "Successfully retrieved searched results",
                            "data": [
                                {
                                    "id": "8e99122a-6646-4d72-bb94-872ba44bf953",
                                    "name": "Crazy Boe",
                                    "property_type__name": "Apartment",
                                    "ad_category__name": "Buy",
                                    "ad_status": "PENDING"
                                },
                                {
                                    "id": "dd4f6e39-a852-4687-8c90-2b2917169530",
                                    "name": "Hanna Montana",
                                    "property_type__name": "Apartment",
                                    "ad_category__name": "Buy",
                                    "ad_status": "PENDING"
                                },
                                {
                                    "id": "691f0273-4c27-40ad-a809-3d7d0fb968d1",
                                    "name": "Property 10",
                                    "property_type__name": "Apartment",
                                    "ad_category__name": "Buy",
                                    "ad_status": "PENDING"
                                }
                            ]
                        }
                    )
                ]
            )
        }
    )
    def get(self, request, *args, **kwargs):
        search = request.query_params.get('search', '')

        get_property_ads = get_searched_property_ads_by_user(user=request.user, search=search)

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
            OpenApiParameter(name='ad_category', description="Type of ad category", required=False,
                             type=OpenApiTypes.STR, enum=AdCategory.objects.values_list('name', flat=True)),
        ],
        tags=['Property'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Successfully retrieved filtered properties",
            )
        }
    )
    def get(self, request):
        queryset = Property.objects.only('id', 'lister', 'name', 'property_state__name', 'property_type__name',
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
                response={'application/json'},
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "status": "success",
                            "message": "Successfully retrieved ad categories",
                            "data": [
                                {
                                    "id": "057dc877-064b-449a-a178-35d02cf80aa1",
                                    "name": "Buy"
                                },
                                {
                                    "id": "5680d436-a4b0-4970-badd-deb735f8dbb4",
                                    "name": "Rent"
                                }
                            ]
                        }
                    )
                ]
            )
        }
    )
    def get(self, request):
        ad_categories = AdCategory.objects.all()

        data = [
            {
                "id": category.id,
                "name": category.name
            }
            for category in ad_categories
        ]
        return CustomResponse.success(message="Successfully retrieved ad categories", data=data)


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
                response={'application/json'},
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "status": "success",
                            "message": "Successfully retrieved property types",
                            "data": [
                                {
                                    "id": "68d42228-703f-4f8c-8843-6ebc452198a7",
                                    "name": "Villa"
                                },
                                {
                                    "id": "6aec02ba-8c5c-445d-bca4-6d3a555095b5",
                                    "name": "Apartment"
                                },
                                {
                                    "id": "6501bbd6-c66d-440b-9b9d-38d18547dbfa",
                                    "name": "House"
                                }
                            ]
                        }
                    )
                ]
            )
        }
    )
    def get(self, request):
        property_types = PropertyType.objects.all()

        data = [
            {
                "id": property_type.id,
                "name": property_type.name
            }
            for property_type in property_types
        ]
        return CustomResponse.success(message="Successfully retrieved property types", data=data)


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
                response={'application/json'},
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "status": "success",
                            "message": "Successfully retrieved property states",
                            "data": [
                                {
                                    "id": "37b76a58-1d46-4799-9d18-ec66d816effc",
                                    "name": "Good condition"
                                },
                                {
                                    "id": "22f06048-4afc-4cb1-accc-66580c0618ec",
                                    "name": "New"
                                },
                                {
                                    "id": "c3b37a05-3978-452d-b118-35ec6e754613",
                                    "name": "Renovated"
                                }
                            ]
                        }
                    )
                ]
            )
        }
    )
    def get(self, request):
        property_states = PropertyState.objects.all()

        data = [
            {
                "id": property_state.id,
                "name": property_state.name
            }
            for property_state in property_states
        ]
        return CustomResponse.success(message="Successfully retrieved property states", data=data)


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
                response={'application/json'},
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "status": "success",
                            "message": "Successfully retrieved property features",
                            "data": [
                                {
                                    "id": "7d288e86-0db7-486e-b80a-106f267f0ffe",
                                    "name": "Storeroom"
                                },
                                {
                                    "id": "c6e1f24f-c7ee-417b-85d8-3e9baac54874",
                                    "name": "Terrace"
                                },
                                {
                                    "id": "dab34afa-5a47-4834-8838-3e443d0818ed",
                                    "name": "Pool"
                                },
                                {
                                    "id": "3e6e7296-3ca4-4757-a252-ce0f34452162",
                                    "name": "Garden"
                                },
                                {
                                    "id": "cf4a37ea-71ee-4b0b-a0f7-2b711353c755",
                                    "name": "On the street"
                                },
                                {
                                    "id": "81bad5cf-875a-4654-b1bd-cfa93b6924cb",
                                    "name": "Elevator"
                                },
                                {
                                    "id": "1c8818f3-3f6f-48e8-9f70-24d729219eeb",
                                    "name": "Wardrobes"
                                },
                                {
                                    "id": "bf9bb2af-a162-4872-aafa-533d15fcbd03",
                                    "name": "Air-Conditioner"
                                }
                            ]
                        }
                    )
                ]
            )
        }
    )
    def get(self, request):
        property_features = PropertyFeature.objects.all()

        data = [
            {
                "id": property_feature.id,
                "name": property_feature.name
            }
            for property_feature in property_features
        ]
        return CustomResponse.success(message="Successfully retrieved property features", data=data)


class CreatePropertyAdView(APIView):
    permission_classes = [IsAuthenticatedAgent]
    serializer_class = CreatePropertyAdSerializer

    @extend_schema(
        summary="Create property ad",
        description="""
        This endpoint allows an authenticated agent to create a new property ad
        Use this endpoint for both buy and sell.
        """,
        tags=['Agent Dashboard'],
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                description="Successfully created property ad",
                response=PropertyAdSerializer
            ),
            status.HTTP_409_CONFLICT: OpenApiResponse(
                description="Property already exists",
                response={'application/json'},
                examples=[
                    OpenApiExample(
                        name="Conflict response",
                        value={
                            "status": "failure",
                            "message": "Property already exists",
                            "code": "already_exists"
                        }
                    )
                ]
            )
        }
    )
    @transaction.atomic
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data

        serialized_data = handle_property_creation(validated_data=validated_data, user=request.user)
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
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=PropertyAdSerializer,
                description="Successfully retrieved property ad"
            ),
        }
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
        responses={
            status.HTTP_202_ACCEPTED: OpenApiResponse(
                response=PropertyAdSerializer,
                description="Successfully updated property ad"
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response={'application/json'},
                description="An error occurred while updating the property ad",
                examples=[
                    OpenApiExample(
                        name="Other error",
                        value={
                            "status": "failure",
                            "message": "An error occurred while updating the property ad",
                            "code": "other_error"
                        }
                    )
                ]
            )
        }
    )
    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        property_id = kwargs.get('id')
        property_ad = get_property_for_user(request.user, property_id=property_id)

        if not property_ad:
            raise RequestError(status_code=status.HTTP_404_NOT_FOUND, err_msg="Property not found",
                               err_code=ErrorCode.NON_EXISTENT)

        serializer = self.serializer_class(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        update_property(serialized_data=data, property_ad=property_ad)

        serialized_data = PropertyAdSerializer(property_ad).data
        return CustomResponse.success(message="Successfully updated property ad", data=serialized_data,
                                      status_code=status.HTTP_202_ACCEPTED)

    @extend_schema(
        summary="Delete property ad",
        description="""
            This endpoint allows an authenticated agent to delete a property ad
            """,
        tags=['Agent Dashboard'],
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                description="Successfully deleted property ad",
                response={'application/json'},
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "status": "success",
                            "message": "Successfully deleted property ad"
                        }
                    )
                ]
            )
        }
    )
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        property_id = kwargs.get('id')
        property_ad = get_property_for_user(request.user, property_id=property_id)
        property_ad.delete()
        return CustomResponse.success(message="Successfully deleted property ad",
                                      status_code=status.HTTP_204_NO_CONTENT)


class RetrieveUpdateCompanyProfileView(APIView):
    permission_classes = [IsAuthenticatedAgent]
    serializer_class = CompanyProfileSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = PropertyAdFilter

    @extend_schema(
        summary="Retrieve company profile",
        description="""
        This endpoint allows an authenticated agent to retrieve their profile alongside their listed accepted properties
        """,
        tags=['Company Profile'],
        parameters=[
            OpenApiParameter(name='property_type', description="Type of property", required=False,
                             type=OpenApiTypes.STR, enum=PropertyType.objects.values_list('name', flat=True)),
            OpenApiParameter(name='price_min', description="Minimum price", required=False, type=OpenApiTypes.FLOAT),
            OpenApiParameter(name='price_max', description="Maximum price", required=False, type=OpenApiTypes.FLOAT),
            OpenApiParameter(name='surface_build_min', description="Minimum surface price", required=False,
                             type=OpenApiTypes.FLOAT),
            OpenApiParameter(name='surface_build_max', description="Maximum surface price", required=False,
                             type=OpenApiTypes.FLOAT),
            OpenApiParameter(name='rooms', description="Number of rooms", required=False, type=OpenApiTypes.INT),
            OpenApiParameter(name='floors', description="Number of floors", required=False, type=OpenApiTypes.INT),
            OpenApiParameter(name='features', description="Features", required=False, type=OpenApiTypes.STR,
                             enum=PropertyFeature.objects.values_list('name', flat=True), many=True),
            OpenApiParameter(name='last_week', description="Filter by properties posted in the last week",
                             required=False, type=OpenApiTypes.BOOL),
            OpenApiParameter(name='last_month', description="Filter by properties posted in the last month",
                             required=False, type=OpenApiTypes.BOOL),
            OpenApiParameter(name='last_24_hours', description="Filter by properties posted in the last 24 hours",
                             required=False, type=OpenApiTypes.BOOL),
        ],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Successfully retrieved company profile",
                response={"application/json"},
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "status": "success",
                            "message": "Successfully retrieved company profile",
                            "data": {
                                "company_info": {
                                    "user_id": "59af4ef1-8e58-47cf-9f1a-e7bae786b883",
                                    "id": "542ee57a-7a5e-4332-a9a7-4de9a775e570",
                                    "full_name": "John Doe",
                                    "company_name": "John Realtor",
                                    "email": "admin@gmail.com",
                                    "image": "/media/static/profile_images/Screenshot_from_2024-05-12_17-43-24_GbVly18.png",
                                    "background_image": "/media/static/profile_bg_images/Screenshot_from_2024-05-12_17-43-48_SUuDb6j.png",
                                    "phone_number": "0803764632",
                                    "license_number": "JHFD77WJK",
                                    "location": "Rub",
                                    "website": "https://google.com"
                                },
                                "company_availability": [
                                    {
                                        "start_day": "Tuesday",
                                        "last_day": "Thursday",
                                        "start_time": "08:45:00",
                                        "end_time": "19:00:00"
                                    },
                                    {
                                        "start_day": "Sunday",
                                        "last_day": "Thursday",
                                        "start_time": "09:45:00",
                                        "end_time": "19:00:00"
                                    }
                                ],
                                "total_number_of_ads": 1,
                                "ads": [
                                    {
                                        "property": {
                                            "id": "8e99122a-6646-4d72-bb94-872ba44bf953",
                                            "media_urls": [
                                                "/media/property_media/7179060_1F5N9rZ.jpg",
                                                "/media/property_media/7179095_Lxd9Y9v.jpg",
                                                "/media/property_media/7179104_oWThtIz.jpg"
                                            ],
                                            "discounted_price": 926250,
                                            "lister": "59af4ef1-8e58-47cf-9f1a-e7bae786b883",
                                            "lister_name": "admin@gmail.com",
                                            "property_type": "6aec02ba-8c5c-445d-bca4-6d3a555095b5",
                                            "property_type_name": "Apartment",
                                            "property_state": "c3b37a05-3978-452d-b118-35ec6e754613",
                                            "property_state_name": "Renovated",
                                            "ad_category": "057dc877-064b-449a-a178-35d02cf80aa1",
                                            "ad_category_name": "Buy",
                                            "features": [
                                                "dab34afa-5a47-4834-8838-3e443d0818ed"
                                            ],
                                            "feature_names": [
                                                "Pool"
                                            ],
                                            "name": "Crazy Boe",
                                            "city": "ibadan",
                                            "floors": 10,
                                            "ground_level": True,
                                            "street": "lautech street",
                                            "street_number": 9,
                                            "area": "lautech area",
                                            "number_of_rooms": 10,
                                            "surface_build": 800,
                                            "total_surface": 9000,
                                            "price": 975000,
                                            "discount": 5,
                                            "entry_date": "2023-09-12",
                                            "number_of_balcony": 1,
                                            "car_parking": 5,
                                            "description": "this is a new thing",
                                            "matterport_view_link": "https://dertuyio.com,",
                                            "name_of_lister": "Montan Doe",
                                            "reachable_phone_number": "+234902245678",
                                            "ad_status": "APPROVED",
                                            "terminated": False
                                        },
                                        "first_media_url": "/media/property_media/7179060_1F5N9rZ.jpg"
                                    }
                                ]
                            }
                        }
                    )
                ]
            )
        }
    )
    def get(self, request):
        user = request.user
        company_profile = get_company_profile(user=user)
        company_availability = company_profile.available_days.all()
        serialized_data = self.serializer_class(company_profile).data
        availability_data = CompanyAvailabilitySerializer(company_availability, many=True)
        queryset = Property.objects.filter(lister=user, ad_status=APPROVED, terminated=False)
        filtered_queryset = self.filterset_class(request.GET, queryset=queryset).qs.order_by('-created')
        total_number_of_ads = filtered_queryset.count()

        data = {
            "company_info": serialized_data,
            "company_availability": availability_data.data,
            "total_number_of_ads": total_number_of_ads,
            "ads": [
                {
                    "property": PropertyAdSerializer(each_property).data,
                    "first_media_url": each_property.property_media.first().media.url  # URL of the first media file
                }
                for each_property in filtered_queryset
            ]
        }
        return CustomResponse.success(message="Successfully retrieved company profile", data=data)

    @extend_schema(
        summary="Update company profile",
        description="""
        This endpoint allows an authenticated agent to update their profile
        """,
        tags=['Company Profile'],
        responses={
            status.HTTP_202_ACCEPTED: OpenApiResponse(
                description="Successfully updated company profile",
                response={'application/json'},
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "status": "success",
                            "message": "Successfully updated company profile",
                            "data": {
                                "user_id": "59af4ef1-8e58-47cf-9f1a-e7bae786b883",
                                "id": "542ee57a-7a5e-4332-a9a7-4de9a775e570",
                                "full_name": "John Fow",
                                "company_name": "John Realtor",
                                "email": "ayflix0@gmail.com",
                                "image": "/media/static/profile_images/Screenshot_from_2024-05-12_17-43-24_GbVly18.png",
                                "background_image": "/media/static/profile_bg_images/Screenshot_from_2024-05-12_17-43-48_SUuDb6j.png",
                                "phone_number": "0803764632",
                                "license_number": "JHFD77WJK",
                                "location": "Rub",
                                "website": "https://google.com"
                            }
                        }
                    )
                ]
            )
        }
    )
    @transaction.atomic
    def patch(self, request):
        user = request.user
        company_profile = get_company_profile(user=user)
        serializer = self.serializer_class(company_profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        serialized_data = self.serializer_class(serializer.save()).data
        return CustomResponse.success(message="Successfully updated company profile", data=serialized_data,
                                      status_code=status.HTTP_202_ACCEPTED)


class RegisterCompanyAgentView(APIView):
    permission_classes = [IsAuthenticatedAgent]
    serializer_class = RegisterCompanyAgentSerializer

    @extend_schema(
        summary="Register company agents",
        description="""
        This endpoints allows a company to register all agents that are working for them
        """,
        tags=['Company Profile'],
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                description="Successfully registered company agent",
                response={'application/json'},
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "status": "success",
                            "message": "Successfully registered company agent",
                            "data": {
                                "company_id": "542ee57a-7a5e-4332-a9a7-4de9a775e570",
                                "company_name": "Doe Realtor",
                                "full_name": "Baba",
                                "phone_number": "+23495847453",
                                "image": "/media/static/profile_images/company_agents/Screenshot_from_2024-05-12_17-43-24.png"
                            }
                        }
                    )
                ]
            )
        }
    )
    @transaction.atomic
    def post(self, request):
        user = request.user
        company_profile = get_company_profile(user=user)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        serialized_data = create_company_agent(company_profile=company_profile,
                                               validated_data=serializer.validated_data)
        return CustomResponse.success(message="Successfully registered company agent", data=serialized_data,
                                      status_code=status.HTTP_201_CREATED)


class RetrieveAllCompanyAgentView(APIView):
    permission_classes = [IsAuthenticatedAgent]

    @extend_schema(
        summary="Retrieve all company agents",
        description="""
        This endpoint allows an authenticated company to retrieve all their company agents
        """,
        tags=['Company Profile'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Successfully retrieved company agents",
                response={'application/json'},
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "status": "success",
                            "message": "Successfully retrieved company agents",
                            "data": [
                                {
                                    "id": "47442d0c-779d-4a86-afd9-0434789f9cad",
                                    "full_name": "Baba Doe",
                                    "phone_number": "+2349584745323",
                                    "profile_picture": "/media/static/profile_images/company_agents/Screenshot_from_2024-05-12_17-43-24_hDaIgcA.png"
                                },
                                {
                                    "id": "4a961d6b-6c57-40c0-9910-45d7c7b6e124",
                                    "full_name": "Baba",
                                    "phone_number": "+23495847453",
                                    "profile_picture": "/media/static/profile_images/company_agents/Screenshot_from_2024-05-12_17-43-24.png"
                                }
                            ]
                        }
                    )
                ]
            )
        }
    )
    def get(self, request):
        user = request.user
        company_profile = get_company_profile(user=user)
        all_agents = company_profile.company_agents.all()

        data = [
            {
                "id": agent.id,
                "full_name": agent.full_name,
                "phone_number": agent.phone_number,
                "profile_picture": agent.profile_picture_url
            }
            for agent in all_agents
        ]
        return CustomResponse.success(message="Successfully retrieved company agents", data=data)


class UpdateCompanyAgentView(APIView):
    permission_classes = [IsAuthenticatedAgent]
    serializer_class = RegisterCompanyAgentSerializer

    @extend_schema(
        summary="Update company agent",
        description="""
        This endpoint allows an authenticated company to update its workers agent profile
        """,
        tags=['Company Profile'],
        responses={
            status.HTTP_202_ACCEPTED: OpenApiResponse(
                description="Successfully updated company agent",
                response={'application/json'},
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "status": "success",
                            "message": "Successfully updated company agent",
                            "data": {
                                "full_name": "GadDam",
                                "phone_number": "+4456788",
                                "profile_picture": "/media/static/profile_images/company_agents/Screenshot_from_2024-05-12_17-43-24_hDaIgcA.png"
                            }
                        }
                    )
                ]
            )
        }
    )
    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        agent_id = kwargs.get('agent_id')
        user = request.user
        company_profile = get_company_profile(user=user)
        agent_profile = get_company_agent(company_profile=company_profile, agent_id=agent_id)

        serializer = self.serializer_class(agent_profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serialized_data = self.serializer_class(serializer.save()).data
        return CustomResponse.success(message="Successfully updated company agent", data=serialized_data,
                                      status_code=status.HTTP_202_ACCEPTED)


class CreateCompanyTimeView(APIView):
    permission_classes = [IsAuthenticatedAgent]
    serializer_class = MultipleAvailabilitySerializer

    @extend_schema(
        summary="Create company time",
        description="""
        This endpoint allows an authenticated company to create company time
        """,
        tags=['Company Profile'],
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                description="Successfully created company time",
                response={'application/json'},
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "status": "success",
                            "message": "Successfully created company time",
                        }
                    )
                ]
            ),
        }
    )
    @transaction.atomic
    def post(self, request):
        user = request.user
        company_profile = get_company_profile(user=user)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        availabilities_data = serializer.validated_data.pop('availabilities')

        handle_company_availability_creation(company=company_profile, data=availabilities_data)
        return CustomResponse.success(message="Successfully created company time", status_code=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Update company time",
        description="""
                This endpoint allows an authenticated company to update company available time
                """,
        tags=['Company Profile'],
        responses={
            status.HTTP_202_ACCEPTED: OpenApiResponse(
                description="Successfully updated company availability",
                response={'application/json'},
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "status": "success",
                            "message": "Successfully updated company time",
                        }
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="An availability doesn't exist",
                response={'application/json'},
                examples=[
                    OpenApiExample(
                        name="Not found response",
                        value={
                            "status": "failure",
                            "message": "This availability doesn't exist",
                            "code": "non_existent"
                        }
                    )
                ]
            )
        }
    )
    @transaction.atomic
    def patch(self, request):
        user = request.user
        company_profile = get_company_profile(user=user)
        company_availability = get_company_availability(company_profile=company_profile)
        serializer = self.serializer_class(company_availability, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        availabilities_data = serializer.validated_data.pop('availabilities')

        handle_company_availability_update(company=company_profile, data=availabilities_data)
        return CustomResponse.success(message="Successfully updated company time", status_code=status.HTTP_202_ACCEPTED)


"""
REGISTERED AND UNREGISTERED USERS
"""


class RetrieveAllFavoritesPropertyView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FavoritePropertySerializer

    @extend_schema(
        summary="Retrieve all favorite properties",
        description="""
        This endpoint allows an authenticated user to retrieve all their favorite properties
        """,
        tags=['Favorites'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Successfully retrieved favorite properties",
                response={'application/json'},
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "status": "success",
                            "message": "Successfully retrieved favorite properties",
                            "data": [
                                {
                                    "media_urls": [
                                        "/media/property_media/7179060_1F5N9rZ.jpg",
                                        "/media/property_media/7179095_Lxd9Y9v.jpg",
                                        "/media/property_media/7179104_oWThtIz.jpg"
                                    ],
                                    "discounted_price": 926250,
                                    "lister": "admin@gmail.com",
                                    "lister_name": "John Doe",
                                    "property_type": "6aec02ba-8c5c-445d-bca4-6d3a555095b5",
                                    "property_type_name": "Apartment",
                                    "property_state": "c3b37a05-3978-452d-b118-35ec6e754613",
                                    "property_state_name": "Renovated",
                                    "ad_category": "057dc877-064b-449a-a178-35d02cf80aa1",
                                    "ad_category_name": "Buy",
                                    "features": [
                                        "dab34afa-5a47-4834-8838-3e443d0818ed"
                                    ],
                                    "feature_names": [
                                        "Pool"
                                    ]
                                }
                            ]
                        }
                    )
                ]
            )
        }
    )
    def get(self, request):
        user = request.user
        property_ads = get_favorite_properties(user=user)
        serialized_data = self.serializer_class(property_ads, many=True).data
        return CustomResponse.success(message="Successfully retrieved favorite properties", data=serialized_data)


class CreateDeleteFavoritePropertyView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Add property to favorite properties",
        description="""
        This endpoint allows an authenticated user to add a property to their favorite properties
        """,
        tags=['Favorites'],
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                description="Successfully added property to favorites",
                response={'application/json'},
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "status": "success",
                            "message": "Successfully added property to favorites"
                        }
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Property not found",
                response={'application/json'},
                examples=[
                    OpenApiExample(
                        name="Error response",
                        value={
                            "status": "failure",
                            "message": "Property not found",
                            "code": "non_existent"
                        }
                    )
                ]
            ),
            status.HTTP_409_CONFLICT: OpenApiResponse(
                description="Property already exists in favorites",
                response={'application/json'},
                examples=[
                    OpenApiExample(
                        name="Conflict response",
                        value={
                            "status": "failure",
                            "message": "Property already exists in favorites",
                            "code": "already_exists"
                        }
                    )
                ]
            )
        }
    )
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = request.user
        property_id = kwargs.get('id')
        property_ad = get_single_property(property_id=property_id)

        # Create property object
        try:
            FavoriteProperty.objects.create(property=property_ad, user=user)
        except IntegrityError:
            raise RequestError(err_code=ErrorCode.ALREADY_EXISTS, err_msg="Property already exists in favorites",
                               status_code=status.HTTP_409_CONFLICT)
        return CustomResponse.success(message="Successfully added property to favorites")

    @extend_schema(
        summary="Delete property from favorite properties",
        description="""
        This endpoint allows an authenticated user to delete a property from their favorite properties
        """,
        tags=['Favorites'],
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                description="Successfully deleted property to favorites",
                response={'application/json'},
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "status": "success",
                            "message": "Successfully deleted property to favorites"
                        }
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Property not found",
                response={'application/json'},
                examples=[
                    OpenApiExample(
                        name="Error response",
                        value={
                            "status": "failure",
                            "message": "Property not found",
                            "code": "non_existent"
                        }
                    ),
                    OpenApiExample(
                        name="Error response",
                        value={
                            "status": "failure",
                            "message": "Property not found in favorites list",
                            "code": "non_existent"
                        }
                    ),
                ]
            )
        }
    )
    def delete(self, request, *args, **kwargs):
        user = request.user
        property_id = kwargs.get('id')
        property_ad = get_single_property(property_id=property_id)

        try:
            FavoriteProperty.objects.get(property=property_ad, user=user).delete()
        except FavoriteProperty.DoesNotExist:
            raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="Property not found in favorites list",
                               status_code=status.HTTP_404_NOT_FOUND)

        return CustomResponse.success(message="Successfully deleted property from favorites",
                                      status_code=status.HTTP_204_NO_CONTENT)


class RetrievePropertyAdDetailsView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CreatePropertyAdSerializer

    @extend_schema(
        summary="Retrieve property ad details",
        description="""
            This endpoint allows an authenticated user to retrieve a property ad details
            """,
        tags=['Property'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Successfully retrieved property ad",
                response=PropertyAdSerializer,
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Property not found",
                response={'application/json'},
                examples=[
                    OpenApiExample(
                        name="Error response",
                        value={
                            "status": "failure",
                            "message": "Property not found",
                            "code": "non_existent"
                        }
                    )
                ]
            )
        }
    )
    def get(self, request, *args, **kwargs):
        property_id = kwargs.get('id')
        property_ad = get_single_property(property_id=property_id)

        serialized_data = PropertyAdSerializer(property_ad).data
        return CustomResponse.success(message="Successfully retrieved property ad", data=serialized_data)


class PromoteBuyAdView(APIView):
    serializer_class = PromoteAdSerializer

    @extend_schema(
        summary="Promote buy ad",
        description="""
            This endpoint allows both unauthenticated and authenticated user to request a property(buy/rent) to be promoted
            """,
        tags=['Promote with us'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Successfully promoted property ad",
                response={'application/json'},
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "status": "success",
                            "message": "Successfully submitted ad promotion request"
                        }
                    )
                ]
            )
        }
    )
    @transaction.atomic
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            PromoteAdRequest.objects.create(**serializer.validated_data, buy_or_rent=True)
        except Exception as e:
            raise RequestError(err_code=ErrorCode.OTHER_ERROR, err_msg=str(e), status_code=status.HTTP_400_BAD_REQUEST)

        return CustomResponse.success(message="Successfully submitted ad promotion request")


class PromoteSellAdView(APIView):
    serializer_class = PromoteAdSerializer

    @extend_schema(
        summary="Promote sell ad",
        description="""
            This endpoint allows both unauthenticated and authenticated user to request a property(sell) to be promoted
            """,
        tags=['Promote with us'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Successfully promoted property ad",
                response={'application/json'},
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "status": "success",
                            "message": "Successfully submitted ad promotion request"
                        }
                    )
                ]
            )
        }
    )
    @transaction.atomic
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            PromoteAdRequest.objects.create(**serializer.validated_data, sell=True)
        except Exception as e:
            raise RequestError(err_code=ErrorCode.OTHER_ERROR, err_msg=str(e), status_code=status.HTTP_400_BAD_REQUEST)

        return CustomResponse.success(message="Successfully submitted ad promotion request")


class RetrieveAllPropertyAdListingView(APIView):
    filter_backends = [DjangoFilterBackend]
    filterset_class = PropertyAdListingFilter
    serializer_class = PropertyAdMiniSerializer

    @extend_schema(
        summary="Retrieve all property ad listings",
        description="""
            This endpoint allows an authenticated and unauthenticated user to retrieve all property ads
            """,
        tags=['Property'],
        parameters=[
            OpenApiParameter(name='ad_category', description="Type of ad category", required=False,
                             type=OpenApiTypes.STR, enum=AdCategory.objects.values_list('name', flat=True)),
            OpenApiParameter(name='property_type', description="Type of property", required=False,
                             type=OpenApiTypes.STR, enum=PropertyType.objects.values_list('name', flat=True)),
            OpenApiParameter(name='price_min', description="Minimum price", required=False, type=OpenApiTypes.FLOAT),
            OpenApiParameter(name='price_max', description="Maximum price", required=False, type=OpenApiTypes.FLOAT),
        ],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Successfully retrieved property ads",
                response={'application/json'},
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "status": "success",
                            "message": "Successfully retrieved property ads",
                            "data": {
                                "total_listings": 1,
                                "listings": [
                                    {
                                        "property": {
                                            "id": "8e99122a-6646-4d72-bb94-872ba44bf953",
                                            "image": "/media/property_media/7179060_1F5N9rZ.jpg",
                                            "name": "Crazy Boe",
                                            "ad_category": "057dc877-064b-449a-a178-35d02cf80aa1",
                                            "ad_category_name": "Buy",
                                            "number_of_rooms": 10,
                                            "price": 975000,
                                            "discounted_price": 926250,
                                            "car_parking": 5,
                                            "surface_build": 800,
                                            "total_surface": 9000,
                                            "lister_phone_number": "+12132131212"
                                        }
                                    }
                                ]
                            }
                        }
                    )
                ]
            )
        }
    )
    def get(self, request):
        queryset = Property.objects.filter(ad_status=APPROVED, terminated=False)
        filtered_queryset = self.filterset_class(request.GET, queryset=queryset).qs.order_by('-created')
        total_number_of_ads = filtered_queryset.count()

        serialized_data = {
            "total_listings": total_number_of_ads,
            "listings": [
                {
                    "property": self.serializer_class(each_property).data,
                }
                for each_property in filtered_queryset
            ]
        }
        return CustomResponse.success(message="Successfully retrieved property ads", data=serialized_data)


class SearchPropertyListingsByCityView(APIView):
    serializer_class = PropertyAdMiniSerializer

    @extend_schema(
        summary="Search property listings by city",
        description="""
            This endpoint allows an authenticated and unauthenticated user to search property ads by city
            """,
        tags=['Property'],
        parameters=[
            OpenApiParameter(name='city', description="City", required=True, type=OpenApiTypes.STR),
        ],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Successfully retrieved property ads",
                response={'application/json'},
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "status": "success",
                            "message": "Successfully retrieved property ads",
                            "data": {
                                "total_listings": 1,
                                "listings": [
                                    {
                                        "property": {
                                            "id": "8e99122a-6646-4d72-bb94-872ba44bf953",
                                            "image": "/media/property_media/7179060_1F5N9rZ.jpg",
                                            "name": "Crazy Boe",
                                            "ad_category": "057dc877-064b-449a-a178-35d02cf80aa1",
                                            "ad_category_name": "Buy",
                                            "number_of_rooms": 10,
                                            "price": 975000,
                                            "discounted_price": 926250,
                                            "car_parking": 5,
                                            "surface_build": 800,
                                            "total_surface": 9000,
                                            "lister_phone_number": "+12132131212"
                                        }
                                    }
                                ]
                            }
                        }
                    )
                ]
            )
        }
    )
    def get(self, request, *args, **kwargs):
        search = request.query_params.get('city', '')

        queryset = Property.objects.filter(ad_status=APPROVED, terminated=False, city__icontains=search)
        total_number_of_ads = queryset.count()

        serialized_data = {
            "total_listings": total_number_of_ads,
            "listings": [
                {
                    "property": self.serializer_class(each_property).data,
                }
                for each_property in queryset
            ]
        }
        return CustomResponse.success(message="Successfully retrieved property ads", data=serialized_data)


class SearchAllPropertyListingsView(APIView):
    serializer_class = PropertyAdMiniSerializer

    @extend_schema(
        summary="Search property listings",
        description="""
            This endpoint allows an authenticated and unauthenticated user to search property ads by city
            """,
        tags=['Property'],
        parameters=[
            OpenApiParameter(name='search', description="Search query", required=True, type=OpenApiTypes.STR),
        ],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Successfully retrieved property ads",
                response={'application/json'},
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "status": "success",
                            "message": "Successfully retrieved property ads",
                            "data": {
                                "total_listings": 1,
                                "listings": [
                                    {
                                        "property": {
                                            "id": "8e99122a-6646-4d72-bb94-872ba44bf953",
                                            "image": "/media/property_media/7179060_1F5N9rZ.jpg",
                                            "name": "Crazy Boe",
                                            "ad_category": "057dc877-064b-449a-a178-35d02cf80aa1",
                                            "ad_category_name": "Buy",
                                            "number_of_rooms": 10,
                                            "price": 975000,
                                            "discounted_price": 926250,
                                            "car_parking": 5,
                                            "surface_build": 800,
                                            "total_surface": 9000,
                                            "lister_phone_number": "+12132131212"
                                        }
                                    }
                                ]
                            }
                        }
                    )
                ]
            )
        }
    )
    def get(self, request, *args, **kwargs):
        search = request.query_params.get('search', '')

        get_property_ads = get_searched_property_ads(search=search)

        serialized_data = {
            "total_listings": get_property_ads.count(),
            "listings": [
                {
                    "property": self.serializer_class(each_property).data,
                }
                for each_property in get_property_ads
            ]
        }

        return CustomResponse.success(message="Successfully retrieved searched results", data=serialized_data)


class RequestPropertyTourView(APIView):

    @extend_schema(
        summary="Request property tour",
        description="""
            This endpoint allows an authenticated user to request a property tour
            """,
        tags=['Property'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Successfully submitted property tour request",
                response={'application/json'},
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "status": "success",
                            "message": "Successfully submitted property tour request"
                        }
                    )
                ]
            )
        }
    )
    def get(self, request):
        pass


class ContactAgentView(APIView):
    serializer_class = ContactAgentSerializer

    @extend_schema(
        summary="Contact agent",
        description="""
            This endpoint allows an authenticated user to contact an agent
            """,
        tags=['Property'],
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                description="Successfully submitted contact request",
                response={'application/json'},
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "status": "success",
                            "message": "Successfully submitted contact request"
                        }
                    )
                ]
            )
        }
    )
    @transaction.atomic
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        property_id = data.pop('property_id')

        property_ad = get_single_property(property_id=property_id)

        ContactCompany.objects.create(property=property_ad, company=property_ad.lister, **data)
        return CustomResponse.success(message="Successfully submitted contact request",
                                      status_code=status.HTTP_201_CREATED)
