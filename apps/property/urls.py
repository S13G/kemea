from django.urls import path

from apps.property.views import *

urlpatterns = [
    path('company/dashboard', RetrieveCompanyDashboardView.as_view(), name='agent-dashboard'),
    path('terminate/ad/<str:property_id>', TerminatePropertyAdView.as_view(), name='terminate-property-ad'),
    path('dashboard/search', SearchAgentDashboardView.as_view(), name='search-dashboard'),
    path('property/filter/agent', RetrieveFilteredAdsView.as_view(), name='agent-filtered-ads'),
    path('property/details/<str:id>', RetrievePropertyAdDetailsView.as_view(), name='property-ad-details'),
    path('ads/categories', RetrieveAdCategoriesView.as_view(), name='ad-categories'),
    path('types', RetrievePropertyTypeView.as_view(), name='property-types'),
    path('state', RetrievePropertyStateView.as_view(), name='property-states'),
    path('features', RetrievePropertyFeaturesView.as_view(), name='property-features'),
    path('create/ad', CreatePropertyAdView.as_view(), name='create-property-ad'),
    path('retrieve/update/delete/ad/<str:id>', RetrieveUpdateDeletePropertyAdView.as_view(),
         name='retrieve-update-property-ad'),
    path('company-profile/details', RetrieveUpdateCompanyProfileView.as_view(), name='retrieve-update-delete-agent'),
    path('favorite/properties/<str:id>', CreateDeleteFavoritePropertyView.as_view(),
         name='create-delete-favorite-property'),
    path('favorite/all', RetrieveAllFavoritesPropertyView.as_view(),
         name='retrieve-all-favorite-properties'),
    path('create/agents', RegisterCompanyAgentView.as_view(), name='register-company-agent'),
    path('company/agents/all', RetrieveAllCompanyAgentView.as_view(), name='retrieve-all-company-agents'),
    path('company/agent/<str:agent_id>/update', UpdateCompanyAgentView.as_view(), name='update-company-agent'),
    path('promote/buy', PromoteBuyAdView.as_view(), name='promote-buy-ad'),
    path('promote/sell', PromoteSellAdView.as_view(), name='promote-sell-ad'),
    path('company/availability', CreateCompanyTimeView.as_view(), name='add-company-availability'),
    path('listings/all', RetrieveAllPropertyAdListingView.as_view(), name='retrieve-all-property-ad-listings'),
    path('listings/city', SearchPropertyListingsByCityView.as_view(),
         name='search-property-ad-listings-by-city'),
    path('listings', SearchAllPropertyListingsView.as_view(), name='search-property-ad-listings'),
    path('contact/company', ContactAgentView.as_view(), name='contact-agent'),
]
