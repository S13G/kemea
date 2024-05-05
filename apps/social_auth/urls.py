from django.urls import path

from apps.social_auth.views import *

urlpatterns = [
    path('google-auth', GoogleSocialAuthView.as_view(), name="google-auth")
]
