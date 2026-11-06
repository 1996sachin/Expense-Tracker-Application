from rest_framework import authentication, permissions
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model

User = get_user_model()


class SMSApiKeyAuthentication(authentication.BaseAuthentication):
    """
    Allows authentication via a user's dedicated SMS Ingestion API Key:
    - Header: 'X-Pocketly-Key: pkt_sms_...'
    - Header: 'Authorization: Api-Key pkt_sms_...'
    - Header: 'Authorization: Bearer pkt_sms_...'
    - Query parameter: '?token=pkt_sms_...' or '?key=pkt_sms_...'
    """
    def authenticate(self, request):
        api_key = None

        # 1. Custom header
        if 'HTTP_X_POCKETLY_KEY' in request.META:
            api_key = request.META['HTTP_X_POCKETLY_KEY']

        # 2. Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not api_key and auth_header:
            parts = auth_header.split()
            if len(parts) == 2:
                prefix, token = parts
                if prefix.lower() in ('api-key', 'apikey'):
                    api_key = token
                elif prefix.lower() == 'bearer' and token.startswith('pkt_sms_'):
                    api_key = token

        # 3. Query param fallback for simple automation webhooks
        if not api_key:
            api_key = request.query_params.get('token') or request.query_params.get('key')

        if not api_key:
            return None

        user = User.objects.filter(sms_api_key=api_key).first()
        if not user:
            raise AuthenticationFailed('Invalid or revoked SMS API key.')

        if not user.is_active:
            raise AuthenticationFailed('User account is inactive.')

        return (user, None)


class IsInsertOnly(permissions.BasePermission):
    """
    Principle of Least Privilege:
    The SMS ingestion endpoint allows INSERT (POST) only.
    It rejects any attempt to READ (GET) or DELETE transactions.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return request.method == 'POST'
