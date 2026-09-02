import base64, hashlib, io, secrets
from datetime import timedelta
from cryptography.fernet import Fernet
from django.conf import settings
from django.utils import timezone
import pyotp, qrcode
from .models import MFAChallenge, MFADevice, RecoveryCode, SecurityEvent

def cipher():
    key = settings.MFA_ENCRYPTION_KEY or base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest())
    return Fernet(key)
def encrypt(value): return cipher().encrypt(value.encode()).decode()
def decrypt(value): return cipher().decrypt(value.encode()).decode()
def event(user, event_type, request=None):
    SecurityEvent.objects.create(user=user, event_type=event_type, ip_address=(request.META.get('REMOTE_ADDR') if request else None), user_agent=(request.META.get('HTTP_USER_AGENT','')[:255] if request else ''))
def device_for(user): return MFADevice.objects.get_or_create(user=user)[0]
def create_challenge(user): return MFAChallenge.objects.create(user=user, expires_at=timezone.now()+timedelta(minutes=settings.MFA_CHALLENGE_TIMEOUT_MINUTES))
def available_methods(user):
    d=device_for(user); return [m for m, active in [('totp',d.totp_enabled),('email',d.email_otp_enabled),('recovery',d.enabled)] if active]
def generate_recovery_codes(user):
    RecoveryCode.objects.filter(user=user, used_at__isnull=True).update(used_at=timezone.now())
    codes=[f'{secrets.token_hex(2).upper()}-{secrets.token_hex(2).upper()}' for _ in range(10)]
    RecoveryCode.objects.bulk_create([RecoveryCode(user=user, code_hash=hashlib.sha256(code.encode()).hexdigest()) for code in codes])
    return codes
def qr_data_url(uri):
    image=qrcode.make(uri); out=io.BytesIO(); image.save(out,format='PNG')
    return 'data:image/png;base64,'+base64.b64encode(out.getvalue()).decode()
