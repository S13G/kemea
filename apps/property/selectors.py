from django.db.models import Count, Q
from rest_framework import status

from apps.common.errors import ErrorCode
from apps.common.exceptions import RequestError
from apps.core.models import AgentProfile
from apps.property.models import Property, PropertyMedia, FavoriteProperty


def get_dashboard_details(user):
    return Property.objects.filter(lister=user) \
        .annotate(num_ads=Count('id')) \
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
    return Property.objects.filter(lister=user).filter(Q(name__icontains=search) | Q(ad_status__icontains=search) |
                                                       Q(description__icontains=search),
                                                       Q(property_type__name__icontains=search) |
                                                       Q(ad_category__name__icontains=search)
                                                       ).values('id', 'name', 'property_type__name',
                                                                'ad_category__name', 'ad_status').order_by('-created')


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


def update_property(serialized_data, property_ad, media_data):
    # Update Property fields
    for key, value in serialized_data.items():
        setattr(property_ad, key, value)
    property_ad.save()

    # Update media data (files)
    if media_data:
        for media_item in media_data:
            item_id = media_item.get('id')
            item_file = media_item.get('media')

            if item_id and item_file:
                # Update the image with the corresponding ID
                media_obj = get_property_media(item_id=item_id, property_ad=property_ad)
                media_obj.media = item_file
                media_obj.save()


def get_agent_profile(user):
    try:
        return AgentProfile.objects.select_related('user').get(user=user)
    except AgentProfile.DoesNotExist:
        raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="Agent profile not found",
                           status_code=status.HTTP_404_NOT_FOUND)


def get_favorite_properties(user):
    return FavoriteProperty.objects.filter(lister=user)


def get_single_property(property_id):
    try:
        return Property.objects.get(id=property_id)
    except Property.DoesNotExist:
        raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="Property not found",
                           status_code=status.HTTP_404_NOT_FOUND)
