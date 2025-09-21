# backend/users/test_models.py
import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()

@pytest.mark.django_db
class TestUserModel:
    
    def test_create_user_success(self, user_data):
        """Test crear usuario exitosamente"""
        user = User.objects.create_user(**user_data)
        
        assert user.email == user_data['email']
        assert user.username == user_data['username']
        assert user.first_name == user_data['first_name']
        assert user.last_name == user_data['last_name']
        assert user.phone == user_data['phone']
        assert user.address == user_data['address']
        assert user.role == 'customer'  # Default role
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False
        assert user.check_password(user_data['password'])

    def test_create_admin_user(self, admin_data):
        """Test crear usuario admin"""
        user = User.objects.create_user(**admin_data)
        
        assert user.role == 'admin'
        assert user.is_admin is True

    def test_create_superuser(self):
        """Test crear superusuario"""
        user = User.objects.create_superuser(
            email='super@example.com',
            username='superuser',
            password='superpass123'
        )
        
        assert user.is_superuser is True
        assert user.is_staff is True
        assert user.is_active is True

    def test_user_str_representation(self, user):
        """Test representación string del usuario"""
        expected = f'{user.email} (Customer)'
        assert str(user) == expected

    def test_admin_str_representation(self, admin_user):
        """Test representación string del admin"""
        expected = f'{admin_user.email} (Admin)'
        assert str(admin_user) == expected

    def test_full_name_property(self):
        """Test propiedad full_name"""
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        
        assert user.full_name == 'John Doe'

    def test_full_name_empty(self):
        """Test full_name cuando nombres están vacíos"""
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        
        assert user.full_name == ''

    def test_is_oauth_user_property(self, oauth_user):
        """Test propiedad is_oauth_user"""
        assert oauth_user.is_oauth_user is True

    def test_is_not_oauth_user(self, user):
        """Test usuario no OAuth"""
        assert user.is_oauth_user is False

    def test_unique_email_constraint(self, user_data):
        """Test que el email debe ser único"""
        User.objects.create_user(**user_data)
        
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                email=user_data['email'],  # Same email
                username='differentuser',
                password='testpass123'
            )

    def test_unique_username_constraint(self, user_data):
        """Test que el username debe ser único"""
        User.objects.create_user(**user_data)
        
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                email='different@example.com',
                username=user_data['username'],  # Same username
                password='testpass123'
            )

    def test_email_as_username_field(self):
        """Test que EMAIL_FIELD es el campo de autenticación principal"""
        assert User.USERNAME_FIELD == 'email'
        assert 'username' in User.REQUIRED_FIELDS