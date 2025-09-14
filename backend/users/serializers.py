from rest_framework import serializers
from .models import User

class UserRegistrationSerializer(serializers.ModelSerializer):
    # Campos para la validacion de contrasena
    password = serializers.CharField(write_only=True, required=True)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'first_name', 'last_name', 
                 'password', 'password_confirm', 'phone', 'address']
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already in use")
        return value
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already in use")
        return value
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    is_oauth_user = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'full_name',
                 'role', 'phone', 'address', 'avatar', 'provider', 'is_oauth_user', 'created_at']
        read_only_fields = ['id', 'role', 'provider', 'created_at']

class LoginSerializer(serializers.Serializer):
    """ Serializer para login con email o username"""
    # Campos de autenticacion
    login = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    username = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        login_field = attrs.get('login') or attrs.get('email') or attrs.get('username')
        if not login_field:
            raise serializers.ValidationError("Must include 'login', 'email', or 'username'")
        if not attrs.get('password'):
            raise serializers.ValidationError("Password is required")
        
        return attrs