import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import PasswordResetToken
from .email_service import EmailService


def issue_password_reset(user):
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    PasswordResetToken.objects.filter(user=user, used_at__isnull=True).update(used_at=timezone.now())
    PasswordResetToken.objects.create(user=user, token_hash=token_hash, expires_at=timezone.now() + timedelta(minutes=settings.PASSWORD_RESET_TIMEOUT_MINUTES))
    reset_url = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?token={raw_token}"
    EmailService.send_password_reset_email(user, reset_url)


def hash_reset_token(raw_token):
    return hashlib.sha256(raw_token.encode()).hexdigest()
