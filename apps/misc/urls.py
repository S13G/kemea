from django.urls import path

from apps.misc.views import *

urlpatterns = [
    path('policy', RetrievePoliciesView.as_view(), name="retrieve-policies"),
]
