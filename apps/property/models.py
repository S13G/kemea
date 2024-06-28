from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models

from apps.common.models import BaseModel
from apps.core.validators import validate_phone_number
from apps.property.choices import AD_STATUS, PENDING
from apps.property.managers import PropertyManager, FavoritePropertyManager

User = get_user_model()


# Create your models here.

class AdCategory(BaseModel):
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = 'Ad Categories'

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
    name = models.CharField(max_length=255)
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
    reachable_phone_number = models.CharField(max_length=255, null=True, validators=[validate_phone_number], default='')
    ad_status = models.CharField(max_length=100, choices=AD_STATUS, default=PENDING)
    terminated = models.BooleanField(default=False)

    objects = PropertyManager()

    class Meta:
        verbose_name_plural = 'Properties'

    def __str__(self):
        return self.name

    @property
    def discounted_price(self):
        return round(
            self.price - (self.price * Decimal((self.discount / 100))) if self.discount > 0 else 'No discounted price',
            2)


class PropertyMedia(BaseModel):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='property_media')
    media = models.FileField(upload_to='property_media')

    def __str__(self):
        return self.property.name


class FavoriteProperty(BaseModel):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='favorite_property')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_property_user')

    objects = FavoritePropertyManager()

    class Meta:
        unique_together = ('property', 'user')

    def __str__(self):
        return self.user.full_name


class PromoteAdRequest(BaseModel):
    location = models.CharField(max_length=255)
    property_type = models.CharField(max_length=255)
    surface = models.PositiveIntegerField(default=0)
    rooms = models.PositiveIntegerField(default=0)
    desired_price = models.DecimalField(max_digits=10, decimal_places=2)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email_address = models.EmailField()
    phone_number = models.CharField(max_length=30, validators=[validate_phone_number])
    buy_or_rent = models.BooleanField(default=False)
    sell = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.location} - {self.desired_price}"


class ContactCompany(BaseModel):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='property_contact')
    company = models.ForeignKey(User, on_delete=models.CASCADE, related_name='company_contact')
    name = models.CharField(max_length=255)
    email_address = models.EmailField()
    phone_number = models.CharField(max_length=30, validators=[validate_phone_number])
    message = models.TextField()

    class Meta:
        verbose_name_plural = "Contact Companies"

    def __str__(self):
        return self.name
