from rest_framework import serializers as sr

from apps.property.models import PropertyType, AdCategory, PropertyState, PropertyFeature, Property


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


class PropertyAdSerializer(sr.Serializer):
    media_urls = sr.SerializerMethodField()

    class Meta:
        model = Property
        exclude = ['created', 'updated']

    @staticmethod
    def get_media_urls(obj):
        media_urls = []
        for media in obj.media:
            media_urls.append(media.media.url)
        return media_urls
