import random
import string
from uuid import uuid4

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from rest_framework_simplejwt.tokens import RefreshToken

from apps.common.models import BaseModel
from apps.core.managers import CustomUserManager


# Create your models here.


class User(AbstractBaseUser, BaseModel, PermissionsMixin):
    full_name = models.CharField(max_length=255, null=True)
    email = models.EmailField(max_length=255, unique=True)
    email_verified = models.BooleanField(default=False)
    google_provider = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    referral_code = models.CharField(max_length=10, null=True)

    USERNAME_FIELD = 'email'

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.email} -- {self.full_name}"

    def save(self, *args, **kwargs):
        if not self.referral_code:
            existing_codes = User.objects.values_list('referral_code', flat=True)
            while True:
                code = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
                if code not in existing_codes:
                    self.referral_code = code
                    break
        super().save(*args, **kwargs)

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


class Profile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, related_name='profile')
    avatar = models.ImageField(upload_to="static/profile_images", null=True, blank=True)
    date_of_birth = models.DateField(null=True)
    phone_number = models.CharField(max_length=100, null=True)
    followers = models.PositiveIntegerField(default=0)
    tokens = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user.full_name} -- {self.user.username}"

    @property
    def profile_image_url(self):
        return self.avatar.url if self.avatar else ""


class Referral(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name="referrals")
    earnings = models.PositiveIntegerField(default=0)
    num_of_referrals = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user.full_name} --> {self.earnings}"
