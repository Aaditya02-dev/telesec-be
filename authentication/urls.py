from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    ForgotPasswordView,
    LoginView,
    RegisterView,
    ResetPasswordView,
    UserDetailView,
    VerifyEmailView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('login/', LoginView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify_email'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('me/', UserDetailView.as_view(), name='user_detail'),
]
