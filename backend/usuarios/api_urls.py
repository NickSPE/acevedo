from django.urls import path
from .api_views import (
    SendVerificationCodeView,
    RegistroUsuarioView,
    UserProfileView,
    CompleteOnboardingView,
    ValidateAccesoRapidoView,
    PasswordResetRequestView,
    CustomLoginView,
    CustomTokenRefreshView,
    CustomLogoutView,
    PINLoginAPIView,
)

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='api_login'),
    path('login/pin/', PINLoginAPIView.as_view(), name='api_login_pin'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='api_token_refresh'),
    path('logout/', CustomLogoutView.as_view(), name='api_logout'),
    path('register/send-code/', SendVerificationCodeView.as_view(), name='api_register_send_code'),
    path('register/', RegistroUsuarioView.as_view(), name='api_register'),
    path('profile/', UserProfileView.as_view(), name='api_user_profile'),
    path('onboarding/', CompleteOnboardingView.as_view(), name='api_complete_onboarding'),
    path('acceso-rapido/validate/', ValidateAccesoRapidoView.as_view(), name='api_acceso_rapido_validate'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='api_password_reset'),
]


