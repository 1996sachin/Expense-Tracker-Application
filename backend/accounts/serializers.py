from django.contrib.auth import get_user_model
from rest_framework import serializers
User = get_user_model()
class UserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='get_full_name', read_only=True)
    class Meta: model = User; fields = ['id','email','name','first_name','last_name','currency_preference','avatar','auth_provider']
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
