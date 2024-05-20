from django.db import IntegrityError
from django.db.models import Q
from rest_framework import status

from apps.common.errors import ErrorCode
from apps.common.exceptions import RequestError
from apps.core.models import CompanyProfile, CompanyAgent, CompanyAvailability
from apps.property.models import Property, PropertyMedia, FavoriteProperty, PropertyFeature
from apps.property.serializers import PropertyAdSerializer


def get_dashboard_details(user):
    return Property.objects.filter(lister=user) \
        .values('id', 'name', 'property_type__name', 'ad_category__name', 'ad_status') \
        .order_by('-created')


def terminate_property_ad(user, ad_id):
    try:
        property_ad = Property.objects.get(lister=user, id=ad_id)

        # if the ad has already been terminated
        if property_ad.terminated:
            raise RequestError(err_code=ErrorCode.NOT_ALLOWED, err_msg="Ad already terminated",
                               status_code=status.HTTP_400_BAD_REQUEST)

        property_ad.terminated = True
        property_ad.save()
    except Property.DoesNotExist:
        raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="Property not found",
                           status_code=status.HTTP_404_NOT_FOUND)


def get_searched_property_ads(user, search):
    return (Property.objects.filter(Q(name__icontains=search) | Q(ad_status__icontains=search) |
                                    Q(description__icontains=search) |
                                    Q(property_type__name__icontains=search) |
                                    Q(ad_category__name__icontains=search),
                                    lister=user)
            .values('id', 'name', 'property_type__name',
                    'ad_category__name', 'ad_status').order_by('-created'))


def get_property_for_user(user, property_id):
    try:
        return Property.objects.get(lister=user, id=property_id)
    except Property.DoesNotExist:
        raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="Property not found",
                           status_code=status.HTTP_404_NOT_FOUND)


def get_property_media(item_id, property_ad):
    try:
        return PropertyMedia.objects.select_related('property').get(id=item_id, property=property_ad)
    except PropertyMedia.DoesNotExist:
        raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="Property not found",
                           status_code=status.HTTP_404_NOT_FOUND)


def update_property(serialized_data, property_ad):
    try:
        # Update specific fields from validated data (excluding features and media)
        for key, value in serialized_data.items():
            if key not in ('features', 'media'):
                setattr(property_ad, key, value)

        # Update features (ManyToMany)
        features = serialized_data.get('features')
        if features:
            update_features(property_ad, features)

        # Update media data (files)
        media = serialized_data.get('media')
        if media:
            update_media(property_ad, media_data=media)

        property_ad.save()

    except Exception as e:
        raise RequestError(err_code=ErrorCode.OTHER_ERROR, status_code=status.HTTP_400_BAD_REQUEST,
                           err_msg=f"An error occurred while updating the property ad: {e}")


def update_features(property_ad, features):
    existing_features = list(property_ad.features.all())  # Get existing features

    # Identify features to add or remove (set difference)
    features_to_add = set(features) - set(existing_features)
    features_to_remove = set(existing_features) - set(features)

    # Add new features
    if features_to_add:
        feature_instances = PropertyFeature.objects.filter(name__in=features_to_add)
        property_ad.features.add(*feature_instances)

    # Remove unwanted features
    property_ad.features.remove(*features_to_remove)


def update_media(property_ad, media_data):
    existing_images = PropertyMedia.objects.filter(property=property_ad)

    # Delete existing images only if new images are provided
    if media_data:
        existing_images.delete()

        # Create new PropertyImage objects for each uploaded image
        property_images = [
            PropertyMedia(property=property_ad, media=image_data)
            for image_data in media_data
        ]
        PropertyMedia.objects.bulk_create(property_images)


def get_company_profile(user):
    try:
        return CompanyProfile.objects.select_related('user').get(user=user)
    except CompanyProfile.DoesNotExist:
        raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="Company profile not found",
                           status_code=status.HTTP_404_NOT_FOUND)


def get_company_availability(company_profile):
    try:
        return CompanyAvailability.objects.select_related('company').filter(company=company_profile)
    except CompanyProfile.DoesNotExist:
        raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="Availability not found",
                           status_code=status.HTTP_404_NOT_FOUND)


def get_favorite_properties(user):
    return FavoriteProperty.objects.filter(user=user)


def get_single_property(property_id):
    try:
        return Property.objects.get(id=property_id)
    except Property.DoesNotExist:
        raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="Property not found",
                           status_code=status.HTTP_404_NOT_FOUND)


def handle_property_creation(validated_data, user):
    # Pop off features which are many to many
    features = validated_data.pop('features', [])

    # Handle media files
    media_data = validated_data.pop('media', [])

    # Create property ad
    try:
        property_ad = Property.objects.create(lister=user, **validated_data)

        # Add features if features exists
        if features:
            feature_instances = PropertyFeature.objects.filter(name__in=features)
            property_ad.features.add(*feature_instances)

        # Add media data if media data exists
        if media_data:
            media_instances = [PropertyMedia(property=property_ad, media=item) for item in media_data]
            PropertyMedia.objects.bulk_create(media_instances)

    except IntegrityError:
        raise RequestError(err_code=ErrorCode.ALREADY_EXISTS, err_msg="Property already exists",
                           status_code=status.HTTP_409_CONFLICT)

    return PropertyAdSerializer(property_ad).data


def create_company_agent(company_profile, validated_data):
    created_profile = CompanyAgent.objects.create(company=company_profile, **validated_data)
    return {
        "company_id": company_profile.id,
        "company_name": company_profile.company_name,
        "full_name": created_profile.full_name,
        "phone_number": created_profile.phone_number,
        "image": created_profile.profile_picture_url
    }


def get_company_agent(company_profile, agent_id):
    try:
        return CompanyAgent.objects.get(company=company_profile, id=agent_id)
    except CompanyAgent.DoesNotExist:
        raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="Agent not found",
                           status_code=status.HTTP_404_NOT_FOUND)


def handle_company_availability_creation(company, data):
    availabilities = []
    for availability_data in data:
        availabilities.append(CompanyAvailability(company=company, **availability_data))

    CompanyAvailability.objects.bulk_create(availabilities)


def handle_company_availability_update(company, data):
    for availability_data in data:
        start_day = availability_data['start_day']
        last_day = availability_data['last_day']

        # Fetch the specific availability record
        try:
            availability = CompanyAvailability.objects.get(
                company=company,
                start_day=start_day,
                last_day=last_day
            )
            # Update the fields
            availability.start_time = availability_data['start_time']
            availability.end_time = availability_data['end_time']
            availability.save()
        except CompanyAvailability.DoesNotExist:
            # If it does not exist, specify error
            raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="An availability doesn't exist",
                               status_code=status.HTTP_404_NOT_FOUND)
