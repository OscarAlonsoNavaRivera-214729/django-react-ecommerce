# backend/users/conftest.py
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

@pytest.fixture
def api_client():
    """Cliente API para las pruebas"""
    return APIClient()

@pytest.fixture
def user_data():
    """Datos de prueba para crear usuario"""
    return {
        'email': 'test@example.com',
        'username': 'testuser',
        'password': 'testpass123',
        'first_name': 'Test',
        'last_name': 'User',
        'phone': '1234567890',
        'address': 'Test Address 123'
    }

@pytest.fixture
def admin_data():
    """Datos de prueba para crear admin"""
    return {
        'email': 'admin@example.com',
        'username': 'adminuser',
        'password': 'adminpass123',
        'first_name': 'Admin',
        'last_name': 'User',
        'role': 'admin'
    }

@pytest.fixture
def user(db, user_data):
    """Usuario de prueba"""
    return User.objects.create_user(**user_data)

@pytest.fixture
def admin_user(db, admin_data):
    """Usuario admin de prueba"""
    return User.objects.create_user(**admin_data)

@pytest.fixture
def oauth_user(db):
    """Usuario OAuth de prueba"""
    return User.objects.create_user(
        email='oauth@example.com',
        username='oauthuser',
        provider='google',
        provider_id='123456789',
        avatar='https://example.com/avatar.jpg'
    )

@pytest.fixture
def authenticated_client(api_client, user):
    """Cliente API autenticado"""
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client

@pytest.fixture
def admin_client(api_client, admin_user):
    """Cliente API autenticado como admin"""
    refresh = RefreshToken.for_user(admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client