from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import AppleLoginView, EmailMFAEnableView, ForgotPasswordView, GoogleLoginView, LoginSessionListView, LoginSessionRevokeView, LoginView, LogoutView, MFASendEmailCodeView, MFAStatusView, MFAVerifyView, ProfileView, RecoveryCodesView, RegisterView, ResetPasswordView, TOTPEnableView, TOTPSetupView, TestEmailView
urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', ProfileView.as_view(), name='profile'),
    path('sessions/', LoginSessionListView.as_view(), name='login-sessions'),
    path('sessions/<int:pk>/', LoginSessionRevokeView.as_view(), name='login-session-revoke'),
    path('google/', GoogleLoginView.as_view(), name='google-login'),
    path('apple/', AppleLoginView.as_view(), name='apple-login'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('mfa/status/', MFAStatusView.as_view(), name='mfa-status'),
    path('mfa/setup/totp/', TOTPSetupView.as_view(), name='totp-setup'),
    path('mfa/enable/totp/', TOTPEnableView.as_view(), name='totp-enable'),
    path('mfa/enable/email/', EmailMFAEnableView.as_view(), name='email-mfa-enable'),
    path('mfa/send-email-code/', MFASendEmailCodeView.as_view(), name='mfa-send-email-code'),
    path('mfa/verify/', MFAVerifyView.as_view(), name='mfa-verify'),
    path('mfa/recovery-codes/', RecoveryCodesView.as_view(), name='mfa-recovery-codes'),
    path('test-email/', TestEmailView.as_view(), name='test-email'),
]

