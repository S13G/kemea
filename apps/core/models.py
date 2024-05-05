from uuid import uuid4

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from rest_framework_simplejwt.tokens import RefreshToken

from apps.common.models import BaseModel
from apps.core.managers import CustomUserManager
from apps.core.validators import validate_phone_number


# Create your models here.


class User(AbstractBaseUser, BaseModel, PermissionsMixin):
    full_name = models.CharField(max_length=255, null=True)
    email = models.EmailField(max_length=255, unique=True)
    phone_number = models.CharField(max_length=100, null=True, validators=[validate_phone_number])
    email_verified = models.BooleanField(default=False)
    google_provider = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_agent = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.email} -- {self.full_name}"

    # Generate JWT tokens for the user(using this specifically for oauth)
    def tokens(self):
        refresh = RefreshToken.for_user(self)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        }


class OTPSecret(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="otp_secret", null=True)
    secret = models.CharField(max_length=255, null=True)
    code = models.PositiveIntegerField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.email


class AgentProfile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, related_name='agent_profile')
    company_name = models.CharField(max_length=255, null=True)
    license_number = models.CharField(max_length=255, null=True)
    image = models.ImageField(upload_to="static/profile_images", null=True, blank=True)
    background_image = models.ImageField(upload_to="static/profile_bg_images", null=True, blank=True)
    location = models.CharField(max_length=255, null=True)
    website = models.CharField(max_length=255, null=True)

    def __str__(self):
        return f"{self.user.full_name} -- {self.user.full_name}"

    @property
    def profile_image_url(self):
        return self.image.url if self.image else ""

    @property
    def background_image_url(self):
        return self.background_image.url if self.background_image else ""


class NormalProfile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, related_name='profile')
    image = models.ImageField(upload_to="static/profile_images", null=True, blank=True)
    date_of_birth = models.DateField(null=True)

    def __str__(self):
        return f"{self.user.full_name} -- {self.user.full_name}"

    @property
    def profile_image_url(self):
        return self.image.url if self.image else ""
