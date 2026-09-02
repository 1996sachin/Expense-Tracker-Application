import os
import jwt
import requests as http_requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.utils import timezone
from google.auth.transport import requests
from google.oauth2 import id_token
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import LoginSession, MFAChallenge, PasswordResetToken
from .serializers import ForgotPasswordSerializer, LoginSessionSerializer, RegisterSerializer, ResetPasswordSerializer, UserSerializer
from .services import get_client_ip, get_ip_location, hash_reset_token, issue_password_reset, parse_device_info
from .email_service import EmailService
from .mfa_service import available_methods, create_challenge, decrypt, device_for, encrypt, event, generate_recovery_codes, qr_data_url
import hashlib, secrets, pyotp
from django.contrib.auth import authenticate

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    def perform_create(self, serializer):
        user = serializer.save()
        event(user, 'USER_REGISTERED', self.request)
        EmailService.safe_send('send_welcome_email', user)

def auth_result(user, request, is_new=False, event_name='PASSWORD_LOGIN'):
    methods = available_methods(user)
    if methods:
        challenge = create_challenge(user)
        return Response({'mfa_required': True, 'challenge_id': str(challenge.id), 'methods': methods})
    event(user, event_name, request)
    if is_new: EmailService.safe_send('send_welcome_email', user)
    if settings.SEND_LOGIN_NOTIFICATION_EMAIL: EmailService.safe_send('send_login_notification', user, timezone.now(), request.META.get('REMOTE_ADDR', 'Unknown'))
    return jwt_response(user, request)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        email=request.data.get('email','').strip().lower(); key=f"login:{email or request.META.get('REMOTE_ADDR','unknown')}"
        if cache.get(key, 0) >= 5: return Response({'detail':'This account is temporarily locked. Try again in 15 minutes.'}, status=429)
        password=request.data.get('password','')
        user=authenticate(request, email=email, password=password)
        if not user:
            cache.set(key, cache.get(key,0)+1, 900)
            return Response({'detail':'Invalid email or password.'}, status=status.HTTP_401_UNAUTHORIZED)
        cache.delete(key)
        return auth_result(user, request)

class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    def get_object(self): return self.request.user

def jwt_response(user, request=None):
    refresh = RefreshToken.for_user(user)
    jti = refresh.get('jti', '')
    ip = get_client_ip(request) if request else None
    ua = request.META.get('HTTP_USER_AGENT', '') if request else ''
    device = parse_device_info(ua)
    loc = get_ip_location(ip)

    session = LoginSession.objects.create(
        user=user,
        ip_address=ip or None,
        device=device,
        user_agent=ua[:512],
        location=loc,
        refresh_token_jti=jti,
    )

    refresh['session_id'] = session.id
    refresh.access_token['session_id'] = session.id

    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': UserSerializer(user).data,
        'session_id': session.id,
    })


class GoogleLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        if not client_id: return Response({'detail': 'Google sign-in is not configured.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        try: payload = id_token.verify_oauth2_token(request.data['credential'], requests.Request(), client_id)
        except Exception: return Response({'detail': 'Invalid Google credential.'}, status=status.HTTP_400_BAD_REQUEST)
        if not payload.get('email_verified') or not payload.get('sub') or not payload.get('email'):
            return Response({'detail': 'Google account email is not verified.'}, status=status.HTTP_400_BAD_REQUEST)
        User = get_user_model()
        is_new = False
        try:
            with transaction.atomic():
                user = User.objects.filter(google_id=payload['sub']).first()
                if not user:
                    user = User.objects.select_for_update().filter(email__iexact=payload['email']).first()
                    if user:
                        if user.google_id and user.google_id != payload['sub']:
                            return Response({'detail': 'This email is already linked to another Google account.'}, status=status.HTTP_409_CONFLICT)
                        user.google_id = payload['sub']; user.auth_provider = 'email' if user.has_usable_password() else 'google'; user.save(update_fields=['google_id', 'auth_provider'])
                    else:
                        base = payload['email'].split('@')[0][:140]; username, index = base, 1
                        while User.objects.filter(username=username).exists(): username = f'{base[:130]}-{index}'; index += 1
                        user = User.objects.create_user(email=payload['email'], username=username, google_id=payload['sub'], auth_provider='google', first_name=payload.get('given_name', ''), last_name=payload.get('family_name', '')); is_new = True
                        user.set_unusable_password(); user.save(update_fields=['password'])
        except IntegrityError: return Response({'detail': 'Unable to link this Google account. Please try again.'}, status=status.HTTP_409_CONFLICT)
        return auth_result(user, request, is_new=is_new, event_name='GOOGLE_LOGIN')

class AppleLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        client_id = os.getenv('APPLE_CLIENT_ID')
        token = request.data.get('identity_token')
        if not client_id: return Response({'detail': 'Apple sign-in is not configured.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        if not token: return Response({'detail': 'Apple identity token is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            header = jwt.get_unverified_header(token)
            keys = http_requests.get('https://appleid.apple.com/auth/keys', timeout=5).json()['keys']
            key = next(item for item in keys if item['kid'] == header['kid'])
            payload = jwt.decode(token, jwt.algorithms.RSAAlgorithm.from_jwk(key), algorithms=['RS256'], audience=client_id, issuer='https://appleid.apple.com')
        except Exception:
            return Response({'detail': 'Invalid Apple credential.'}, status=status.HTTP_400_BAD_REQUEST)
        if not payload.get('sub') or not payload.get('email'): return Response({'detail': 'Apple did not provide a verified email address.'}, status=status.HTTP_400_BAD_REQUEST)
        User = get_user_model(); is_new = False
        with transaction.atomic():
            user = User.objects.filter(apple_id=payload['sub']).first() or User.objects.select_for_update().filter(email__iexact=payload['email']).first()
            if user:
                if user.apple_id and user.apple_id != payload['sub']: return Response({'detail': 'This email is linked to another Apple account.'}, status=status.HTTP_409_CONFLICT)
                user.apple_id = payload['sub']; user.auth_provider = 'email' if user.has_usable_password() else 'apple'; user.save(update_fields=['apple_id', 'auth_provider'])
            else:
                base = payload['email'].split('@')[0][:140]; username = base; index = 1
                while User.objects.filter(username=username).exists(): username = f'{base[:130]}-{index}'; index += 1
                user = User.objects.create_user(email=payload['email'], username=username, apple_id=payload['sub'], auth_provider='apple'); user.set_unusable_password(); user.save(update_fields=['password']); is_new = True
        return auth_result(user, request, is_new=is_new, event_name='APPLE_LOGIN')

class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data); serializer.is_valid(raise_exception=True)
        if not cache.add(f"password-reset:{request.META.get('REMOTE_ADDR', 'unknown')}", '1', timeout=60):
            return Response({'detail': 'Please wait a minute before requesting another reset link.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        user = get_user_model().objects.filter(email__iexact=serializer.validated_data['email']).first()
        if user:
            try: issue_password_reset(user)
            except Exception: pass
        return Response({'detail': "If an account exists with this email, we've sent you a password reset link."})

class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data); serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            reset = PasswordResetToken.objects.select_for_update().filter(token_hash=hash_reset_token(serializer.validated_data['token']), used_at__isnull=True, expires_at__gt=timezone.now()).select_related('user').first()
            if not reset: return Response({'detail': 'This password reset link is invalid or has expired.'}, status=status.HTTP_400_BAD_REQUEST)
            reset.user.set_password(serializer.validated_data['password']); reset.user.auth_provider = 'email'; reset.user.save(update_fields=['password', 'auth_provider'])
            reset.used_at = timezone.now(); reset.save(update_fields=['used_at'])
            PasswordResetToken.objects.filter(user=reset.user, used_at__isnull=True).exclude(pk=reset.pk).update(used_at=timezone.now())
        return Response({'detail': 'Password reset successfully. You can now sign in.'})

class MFAStatusView(APIView):
    def get(self, request):
        d=device_for(request.user); return Response({'totp_enabled':d.totp_enabled,'email_otp_enabled':d.email_otp_enabled,'recovery_codes_remaining':request.user.recovery_codes.filter(used_at__isnull=True).count()})

class TOTPSetupView(APIView):
    def post(self, request):
        d=device_for(request.user); secret=pyotp.random_base32(); d.pending_totp_secret_encrypted=encrypt(secret); d.save(update_fields=['pending_totp_secret_encrypted'])
        uri=pyotp.TOTP(secret).provisioning_uri(name=request.user.email, issuer_name='Pocketly')
        return Response({'qr_code':qr_data_url(uri),'setup_key':secret})

class TOTPEnableView(APIView):
    def post(self, request):
        code=str(request.data.get('code','')).replace(' ',''); d=device_for(request.user)
        if not d.pending_totp_secret_encrypted: return Response({'detail':'Start TOTP setup first.'},status=400)
        secret=decrypt(d.pending_totp_secret_encrypted)
        if not pyotp.TOTP(secret).verify(code, valid_window=1): return Response({'detail':'Invalid verification code.'},status=400)
        d.totp_secret_encrypted=encrypt(secret); d.pending_totp_secret_encrypted=''; d.totp_enabled=True; d.save(update_fields=['totp_secret_encrypted','pending_totp_secret_encrypted','totp_enabled'])
        codes=generate_recovery_codes(request.user); event(request.user,'MFA_ENABLED',request); return Response({'detail':'Authenticator app enabled. Save these recovery codes now.','recovery_codes':codes})

class EmailMFAEnableView(APIView):
    def post(self, request):
        d=device_for(request.user); d.email_otp_enabled=True; d.save(update_fields=['email_otp_enabled']);
        if not request.user.recovery_codes.filter(used_at__isnull=True).exists(): codes=generate_recovery_codes(request.user)
        else: codes=[]
        event(request.user,'MFA_EMAIL_ENABLED',request); return Response({'detail':'Email verification codes enabled.','recovery_codes':codes})

class MFASendEmailCodeView(APIView):
    permission_classes=[permissions.AllowAny]
    def post(self,request):
        try: challenge=MFAChallenge.objects.get(pk=request.data.get('challenge_id'),used_at__isnull=True,locked_at__isnull=True,expires_at__gt=timezone.now())
        except MFAChallenge.DoesNotExist:return Response({'detail':'This sign-in challenge is invalid or expired.'},status=400)
        if 'email' not in available_methods(challenge.user): return Response({'detail':'Email verification is unavailable.'},status=400)
        code=f'{secrets.randbelow(1000000):06d}'; challenge.email_code_hash=hashlib.sha256(code.encode()).hexdigest(); challenge.save(update_fields=['email_code_hash']); EmailService.safe_send('send_email_otp',challenge.user,code)
        return Response({'detail':'A verification code was sent.'})

class MFAVerifyView(APIView):
    permission_classes=[permissions.AllowAny]
    @transaction.atomic
    def post(self,request):
        try: challenge=MFAChallenge.objects.select_for_update().select_related('user').get(pk=request.data.get('challenge_id'),used_at__isnull=True,locked_at__isnull=True,expires_at__gt=timezone.now())
        except MFAChallenge.DoesNotExist:return Response({'detail':'This sign-in challenge is invalid, locked, or expired.'},status=400)
        method=request.data.get('method'); code=str(request.data.get('code','')).strip(); valid=False; d=device_for(challenge.user)
        if method=='totp' and d.totp_enabled: valid=pyotp.TOTP(decrypt(d.totp_secret_encrypted)).verify(code,valid_window=1)
        elif method=='email' and d.email_otp_enabled and challenge.email_code_hash: valid=secrets.compare_digest(challenge.email_code_hash,hashlib.sha256(code.encode()).hexdigest())
        elif method=='recovery':
            recovery=challenge.user.recovery_codes.filter(code_hash=hashlib.sha256(code.upper().encode()).hexdigest(),used_at__isnull=True).first()
            if recovery: recovery.used_at=timezone.now(); recovery.save(update_fields=['used_at']); valid=True; event(challenge.user,'RECOVERY_CODE_USED',request)
        if not valid:
            challenge.attempts+=1
            if challenge.attempts>=5: challenge.locked_at=timezone.now()
            challenge.save(update_fields=['attempts','locked_at']); event(challenge.user,'MFA_FAILURE',request)
            return Response({'detail':'Invalid verification code.'},status=400)
        challenge.used_at=timezone.now(); challenge.save(update_fields=['used_at']); event(challenge.user,'MFA_SUCCESS',request); return jwt_response(challenge.user, request)

class RecoveryCodesView(APIView):
    def post(self,request):
        codes=generate_recovery_codes(request.user); event(request.user,'RECOVERY_CODES_REGENERATED',request); return Response({'recovery_codes':codes})

class TestEmailView(APIView):
    def post(self,request):
        if not request.user.is_staff:return Response({'detail':'Administrator access required.'},status=403)
        email=request.data.get('email')
        if not email:return Response({'detail':'Email is required.'},status=400)
        original=request.user.email; request.user.email=email
        try: EmailService.send_test_email(request.user)
        except Exception:return Response({'detail':'Email could not be sent. Check server email configuration.'},status=503)
        finally: request.user.email=original
        return Response({'message':'Test email sent successfully'})

class LoginSessionListView(generics.ListAPIView):
    serializer_class = LoginSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return LoginSession.objects.filter(user=self.request.user, is_revoked=False).order_by('-login_at')

class LoginSessionRevokeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        session = LoginSession.objects.filter(user=request.user, pk=pk, is_revoked=False).first()
        if not session:
            return Response({'detail': 'Session not found.'}, status=status.HTTP_404_NOT_FOUND)

        session.is_revoked = True
        session.save(update_fields=['is_revoked'])

        if session.refresh_token_jti:
            try:
                from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
                outstanding = OutstandingToken.objects.filter(jti=session.refresh_token_jti).first()
                if outstanding:
                    BlacklistedToken.objects.get_or_create(token=outstanding)
            except Exception:
                pass

        event(request.user, 'SESSION_REVOKED', request)
        return Response({'detail': 'Session revoked successfully.'}, status=status.HTTP_200_OK)

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        auth = getattr(request, 'auth', None)
        session_id = auth.get('session_id') if (auth and (isinstance(auth, dict) or hasattr(auth, 'get'))) else None

        if session_id:
            LoginSession.objects.filter(user=request.user, pk=session_id).update(is_revoked=True)
        elif refresh_token:
            try:
                token = RefreshToken(refresh_token)
                jti = token.get('jti')
                if jti:
                    LoginSession.objects.filter(user=request.user, refresh_token_jti=jti).update(is_revoked=True)
                token.blacklist()
            except Exception:
                pass

        event(request.user, 'LOGOUT', request)
        return Response({'detail': 'Logged out successfully.'}, status=status.HTTP_200_OK)

