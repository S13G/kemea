from django.urls import path

from apps.core import views

urlpatterns = [
    path('verify/email', views.VerifyEmailView.as_view(), name="verify-email"),
    path(
        'resend/email/verify/code/resend',
        views.ResendEmailVerificationCodeView.as_view(),
        name="resend-email-verification-code"
    ),
    path(
        'new-email/verify/code',
        views.SendNewEmailVerificationCodeView.as_view(),
        name="send-new-email-verification-code"
    ),
    path('change/email', views.ChangeEmailView.as_view(), name="change-email"),
    path('login', views.LoginView.as_view(), name="login"),
    path('logout', views.LogoutView.as_view(), name="logout"),
    path('refresh/token', views.RefreshView.as_view(), name="refresh-token"),
    path('request/forgot-password/code', views.RequestForgotPasswordCodeView.as_view(),
         name="request-forgotten-password-code"),
    path('verify/forgot-password/code', views.VerifyForgotPasswordCodeView.as_view(),
         name="verify-forgotten-password-code"),
    path('change/forgot-password/<str:token>', views.ChangeForgottenPasswordView.as_view(),
         name="change-forgotten-password"),
    path('change/new-password', views.ChangePasswordView.as_view(), name="change-password"),
    path('user-account/create', views.NormalRegistrationView.as_view(), name="normal-user-registration"),
    path('company-account/create', views.CompanyRegistrationView.as_view(), name="agent-user-registration"),
    path('user-profile/details', views.RetrieveUpdateProfileView.as_view(),
         name="get-update-delete-profile"),
]
