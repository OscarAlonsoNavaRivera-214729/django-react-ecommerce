# backend/users/test_serializers.py
import pytest
from django.contrib.auth import get_user_model
from users import serializer
from users.serializer import UserRegistrationSerializer, UserSerializer, LoginSerializer

User = get_user_model()

@pytest.mark.django_db
class TestUserRegistrationSerializer:
    
    def test_valid_registration_data(self, user_data):
        """Test serialización con datos válidos"""
        data = user_data.copy()
        data['password_confirm'] = data['password']
        
        serializer = UserRegistrationSerializer(data=data)
        
        assert serializer.is_valid()
        user = serializer.save()
        assert isinstance(user, User)
        assert user.email == data['email']

    def test_password_mismatch(self, user_data):
        """Test cuando las contraseñas no coinciden"""
        data = user_data.copy()
        data['password_confirm'] = 'differentpassword'
        
        serializer = UserRegistrationSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'password' in serializer.errors

    def test_duplicate_email(self, user_data):
        """Test email duplicado"""
        # Crear usuario existente
        User.objects.create_user(**user_data)
        
        # Intentar crear otro con mismo email
        data = user_data.copy()
        data['username'] = 'differentuser'
        data['password_confirm'] = data['password']
        
        serializer = UserRegistrationSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'email' in serializer.errors
        assert 'user with this email already exists.' in str(serializer.errors['email'])

    def test_duplicate_username(self, user_data):
        """Test username duplicado"""
        # Crear usuario existente
        User.objects.create_user(**user_data)
        
        # Intentar crear otro con mismo username
        data = user_data.copy()
        data['email'] = 'different@example.com'
        data['password_confirm'] = data['password']
        
        serializer = UserRegistrationSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'username' in serializer.errors
        assert 'A user with that username already exists.' in str(serializer.errors['username'])

    def test_missing_required_fields(self):
        """Test campos requeridos faltantes"""
        serializer = UserRegistrationSerializer(data={})
        
        assert not serializer.is_valid()
        required_fields = ['email', 'username', 'password', 'password_confirm']
        for field in required_fields:
            assert field in serializer.errors

class TestUserSerializer:
    
    def test_user_serialization(self, user):
        """Test serialización de usuario"""
        serializer = UserSerializer(user)
        data = serializer.data
        
        expected_fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 
            'full_name', 'role', 'phone', 'address', 'avatar', 
            'provider', 'is_oauth_user', 'created_at'
        ]
        
        for field in expected_fields:
            assert field in data
        
        assert data['email'] == user.email
        assert data['full_name'] == user.full_name
        assert data['is_oauth_user'] == user.is_oauth_user

    def test_oauth_user_serialization(self, oauth_user):
        """Test serialización de usuario OAuth"""
        serializer = UserSerializer(oauth_user)
        data = serializer.data
        
        assert data['provider'] == oauth_user.provider
        assert data['avatar'] == oauth_user.avatar
        assert data['is_oauth_user'] is True

    def test_read_only_fields(self, user):
        """Test que campos read-only no se pueden actualizar"""
        original_id = user.id
        original_role = user.role
        original_created_at = user.created_at
        
        data = {
            'id': 999,
            'role': 'admin',
            'created_at': '2020-01-01T00:00:00Z',
            'first_name': 'Updated'
        }
        
        serializer = UserSerializer(user, data=data, partial=True)
        
        if serializer.is_valid():
            updated_user = serializer.save()
            assert updated_user.id == original_id
            assert updated_user.role == original_role
            assert updated_user.created_at == original_created_at
            assert updated_user.first_name == 'Updated'

class TestLoginSerializer:
    
    def test_valid_login_data(self):
        """Test datos de login válidos"""
        data = {
            'login': 'test@example.com',
            'password': 'testpass123'
        }
        
        serializer = LoginSerializer(data=data)
        assert serializer.is_valid()

    def test_email_login(self):
        """Test login con email"""
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        
        serializer = LoginSerializer(data=data)
        assert serializer.is_valid()

    def test_username_login(self):
        """Test login con username"""
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        serializer = LoginSerializer(data=data)
        assert serializer.is_valid()

    def test_missing_login_field(self):
        """Test falta campo de login"""
        data = {
            'password': 'testpass123'
        }
        
        serializer = LoginSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors

    def test_missing_password(self):
        """Test falta contraseña"""
        data = {
            'login': 'test@example.com'
        }
        
        serializer = LoginSerializer(data=data)
        serializer.is_valid()  

        assert 'password' in serializer.errors
        assert serializer.errors['password'][0] == 'This field is required.'