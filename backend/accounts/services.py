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


def get_client_ip(request):
    if not request:
        return ''
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def parse_device_info(user_agent: str) -> str:
    if not user_agent:
        return 'Unknown device'
    ua = user_agent.lower()

    # Browser
    browser = 'Unknown Browser'
    if 'edg/' in ua or 'edge/' in ua:
        browser = 'Microsoft Edge'
    elif 'opr/' in ua or 'opera' in ua:
        browser = 'Opera'
    elif 'chrome/' in ua and 'chromium' not in ua:
        browser = 'Google Chrome'
    elif 'firefox/' in ua:
        browser = 'Mozilla Firefox'
    elif 'safari/' in ua and 'chrome' not in ua:
        browser = 'Apple Safari'
    elif 'postman' in ua:
        browser = 'Postman'
    elif 'curl' in ua:
        browser = 'cURL'
    elif 'python' in ua:
        browser = 'Python Client'

    # Platform / OS
    platform = 'Unknown Platform'
    if 'iphone' in ua:
        platform = 'iPhone (iOS)'
    elif 'ipad' in ua:
        platform = 'iPad (iPadOS)'
    elif 'android' in ua:
        platform = 'Android'
    elif 'mac os' in ua or 'macintosh' in ua:
        platform = 'macOS'
    elif 'windows' in ua:
        platform = 'Windows'
    elif 'linux' in ua:
        platform = 'Linux'

    if browser != 'Unknown Browser' and platform != 'Unknown Platform':
        return f'{browser} on {platform}'
    if browser != 'Unknown Browser':
        return browser
    if platform != 'Unknown Platform':
        return platform
    return user_agent[:60]


def get_ip_location(ip: str) -> str:
    if not ip or ip in ('127.0.0.1', '::1', 'localhost'):
        return 'Localhost'
    if ip.startswith(('10.', '192.168.', '172.16.', '172.17.', '172.18.', '172.19.', '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.', '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.')):
        return 'Local Network'
    return 'Unknown location'

