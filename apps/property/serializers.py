from django.contrib.auth import get_user_model
from rest_framework import serializers as sr

from apps.core.validators import validate_phone_number
from apps.property.models import PropertyType, AdCategory, PropertyState, PropertyFeature, Property

User = get_user_model()


class CreatePropertyAdSerializer(sr.Serializer):
    property_type = sr.PrimaryKeyRelatedField(queryset=PropertyType.objects.all())
    property_state = sr.PrimaryKeyRelatedField(queryset=PropertyState.objects.all())
    ad_category = sr.PrimaryKeyRelatedField(queryset=AdCategory.objects.all())
    name = sr.CharField()
    city = sr.CharField()
    floors = sr.IntegerField()
    ground_level = sr.BooleanField(default=False)
    street = sr.CharField()
    street_number = sr.CharField()
    area = sr.CharField()
    number_of_rooms = sr.IntegerField()
    surface_build = sr.IntegerField()
    total_surface = sr.IntegerField()
    price = sr.DecimalField(max_digits=10, decimal_places=2)
    discount = sr.IntegerField()
    entry_date = sr.DateField()
    number_of_balcony = sr.IntegerField()
    car_parking = sr.IntegerField()
    features = sr.PrimaryKeyRelatedField(many=True, queryset=PropertyFeature.objects.all())
    description = sr.CharField()
    matterport_view_link = sr.CharField()
    media = sr.ListField(child=sr.FileField(), allow_empty=True, max_length=30)
    name_of_lister = sr.CharField()
    reachable_phone_number = sr.CharField(validators=[validate_phone_number])


class PropertyAdSerializer(sr.ModelSerializer):
    media_urls = sr.SerializerMethodField()
    discounted_price = sr.SerializerMethodField()
    lister = sr.PrimaryKeyRelatedField(queryset=User.objects.all())
    lister_name = sr.StringRelatedField(source='lister')
    property_type = sr.PrimaryKeyRelatedField(queryset=PropertyType.objects.all())
    property_type_name = sr.StringRelatedField(source='property_type')
    property_state = sr.PrimaryKeyRelatedField(queryset=PropertyState.objects.all())
    property_state_name = sr.StringRelatedField(source='property_state')
    ad_category = sr.PrimaryKeyRelatedField(queryset=AdCategory.objects.all())
    ad_category_name = sr.StringRelatedField(source='ad_category')
    features = sr.PrimaryKeyRelatedField(many=True, queryset=PropertyFeature.objects.all())
    feature_names = sr.StringRelatedField(many=True, source='features')

    class Meta:
        model = Property
        exclude = ['created', 'updated']

    @staticmethod
    def get_discounted_price(obj):
        return obj.discounted_price

    @staticmethod
    def get_media_urls(obj):
        media_urls = []
        for media in obj.property_media.all():
            media_urls.append(media.media.url)
        return media_urls


class FavoritePropertySerializer(sr.Serializer):
    media_urls = sr.SerializerMethodField()
    discounted_price = sr.SerializerMethodField()
    lister = sr.CharField(source='property.lister')
    lister_name = sr.CharField(source='property.lister.full_name')
    property_type = sr.CharField(source="property.property_type.id", read_only=True)
    property_type_name = sr.CharField(source='property.property_type.name', read_only=True)
    property_state = sr.CharField(source="property.property_state.id", read_only=True)
    property_state_name = sr.CharField(source='property.property_state.name', read_only=True)
    ad_category = sr.CharField(source="property.ad_category.id", read_only=True)
    ad_category_name = sr.CharField(source='property.ad_category.name', read_only=True)
    features = sr.PrimaryKeyRelatedField(many=True, source="property.features", read_only=True)
    feature_names = sr.SerializerMethodField()  # Use the method to retrieve names

    @staticmethod
    def get_feature_names(obj):
        # Access the features using the related manager
        features = obj.property.features.all()
        # Extract the names using list comprehension
        feature_names = [feature.name for feature in features]
        return feature_names

    @staticmethod
    def get_discounted_price(obj):
        return obj.property.discounted_price

    @staticmethod
    def get_media_urls(obj):
        media_urls = []
        for media in obj.property.property_media.all():
            media_urls.append(media.media.url)
        return media_urls


class RegisterCompanyAgentSerializer(sr.Serializer):
    full_name = sr.CharField()
    phone_number = sr.CharField(validators=[validate_phone_number])
    profile_picture = sr.ImageField()

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save()
        return instance
