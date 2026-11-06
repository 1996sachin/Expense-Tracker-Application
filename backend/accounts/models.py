from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
class User(AbstractUser):
    email = models.EmailField(unique=True)
    currency_preference = models.CharField(max_length=3, default=settings.DEFAULT_CURRENCY)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    google_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    auth_provider = models.CharField(max_length=12, default='email')
    sms_api_key = models.CharField(max_length=64, blank=True, null=True, unique=True, db_index=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def get_or_create_sms_api_key(self):
        import secrets
        if not self.sms_api_key:
            self.sms_api_key = f"pkt_sms_{secrets.token_hex(24)}"
            self.save(update_fields=['sms_api_key'])
        return self.sms_api_key

    def rotate_sms_api_key(self):
        import secrets
        self.sms_api_key = f"pkt_sms_{secrets.token_hex(24)}"
        self.save(update_fields=['sms_api_key'])
        return self.sms_api_key


class PasswordResetToken(models.Model):
    """Single-use credentials; only a hash of each raw token is persisted."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['token_hash', 'expires_at'])]

class MFADevice(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mfa_device')
    totp_secret_encrypted = models.TextField(blank=True)
    pending_totp_secret_encrypted = models.TextField(blank=True)
    totp_enabled = models.BooleanField(default=False)
    email_otp_enabled = models.BooleanField(default=False)
    preferred_method = models.CharField(max_length=12, default='totp')
    enabled_at = models.DateTimeField(null=True, blank=True)

    @property
    def enabled(self): return self.totp_enabled or self.email_otp_enabled

class MFAChallenge(models.Model):
    id = models.UUIDField(primary_key=True, default=__import__('uuid').uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mfa_challenges')
    email_code_hash = models.CharField(max_length=64, blank=True)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    locked_at = models.DateTimeField(null=True, blank=True)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class RecoveryCode(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recovery_codes')
    code_hash = models.CharField(max_length=64, unique=True)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class SecurityEvent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='security_events')
    event_type = models.CharField(max_length=48)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['-created_at']
