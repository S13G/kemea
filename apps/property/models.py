from django.contrib.auth import get_user_model
from django.db import models

from apps.common.models import BaseModel
from apps.core.validators import validate_phone_number
from apps.property.choices import AD_STATUS, PENDING
from apps.property.managers import PropertyManager

User = get_user_model()


# Create your models here.

class AdCategory(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class PropertyType(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class PropertyState(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class PropertyFeature(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Property(BaseModel):
    lister = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='property_lister')
    property_type = models.ForeignKey(PropertyType, on_delete=models.CASCADE, null=True, related_name="property_type")
    property_state = models.ForeignKey(PropertyState, on_delete=models.CASCADE, null=True,
                                       related_name="property_state")
    ad_category = models.ForeignKey(AdCategory, on_delete=models.CASCADE, null=True, related_name="ad_category")
    name = models.CharField(max_length=255, unique=True)
    city = models.CharField(max_length=255)
    floors = models.PositiveIntegerField(default=20)
    ground_level = models.BooleanField(default=False)
    street = models.CharField(max_length=255)
    street_number = models.PositiveIntegerField(default=0)
    area = models.CharField(max_length=255)
    number_of_rooms = models.PositiveIntegerField(default=0)
    surface_build = models.PositiveIntegerField(default=0)
    total_surface = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.PositiveIntegerField(default=0)
    entry_date = models.DateField(null=True)
    number_of_balcony = models.PositiveIntegerField(default=1)
    car_parking = models.PositiveIntegerField(default=1)
    features = models.ManyToManyField(PropertyFeature, related_name="property_features", blank=True)
    description = models.TextField()
    matterport_view_link = models.CharField(max_length=255, null=True)
    name_of_lister = models.CharField(max_length=255, null=True)
    reachable_phone_number = models.CharField(max_length=255, null=True, validators=[validate_phone_number])
    ad_status = models.CharField(max_length=100, choices=AD_STATUS, default=PENDING)
    terminated = models.BooleanField(default=False)

    objects = PropertyManager()

    def __str__(self):
        return self.name

    @property
    def discounted_price(self):
        return self.price - (self.price * (self.discount / 100)) if self.discount > 0 else 'No discounted price'


class PropertyMedia(BaseModel):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='property_media')
    media = models.FileField(upload_to='property_media')

    def __str__(self):
        return self.property.name


class FavoriteProperty(BaseModel):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='favorite_property')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_property_user')

    def __str__(self):
        return self.user.full_name
