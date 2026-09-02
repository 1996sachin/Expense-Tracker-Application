from django.contrib.auth import get_user_model
from rest_framework import serializers
User = get_user_model()
class UserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='get_full_name', read_only=True)
    class Meta: model = User; fields = ['id','email','name','first_name','last_name','currency_preference','avatar','auth_provider','onboarding_complete','sex','date_of_birth','language','google_id','apple_id']; read_only_fields = ['google_id','apple_id','auth_provider']
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    class Meta: model = User; fields = ['email','username','password','first_name','last_name','currency_preference']
    def validate_password(self, value):
        from django.contrib.auth.password_validation import validate_password
        validate_password(value)
        return value
    def create(self, data): return User.objects.create_user(**data)

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField(min_length=32, max_length=512, write_only=True)
    password = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)
    def validate_password(self, value):
        from django.contrib.auth.password_validation import validate_password
        validate_password(value)
        return value

class LoginSessionSerializer(serializers.ModelSerializer):
    is_current = serializers.SerializerMethodField()

    class Meta:
        from .models import LoginSession
        model = LoginSession
        fields = ['id', 'ip_address', 'device', 'user_agent', 'location', 'login_at', 'last_active_at', 'is_current']
        read_only_fields = ['id', 'ip_address', 'device', 'user_agent', 'location', 'login_at', 'last_active_at', 'is_current']

    def get_is_current(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        auth = getattr(request, 'auth', None)
        if auth and (isinstance(auth, dict) or hasattr(auth, 'get')):
            session_id = auth.get('session_id')
            if session_id is not None:
                return str(obj.id) == str(session_id)
            jti = auth.get('jti')
            if jti and obj.refresh_token_jti:
                return obj.refresh_token_jti == jti
        from .models import LoginSession
        latest_id = getattr(request, '_latest_session_id', None)
        if latest_id is None:
            latest = LoginSession.objects.filter(user=request.user, is_revoked=False).order_by('-login_at').first()
            latest_id = latest.id if latest else -1
            request._latest_session_id = latest_id
        return obj.id == latest_id

