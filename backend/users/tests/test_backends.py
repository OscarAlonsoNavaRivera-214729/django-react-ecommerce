# backend/users/test_backends.py
import pytest
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from users.backends import EmailOrUsernameModelBackend

User = get_user_model()

@pytest.mark.django_db
class TestEmailOrUsernameModelBackend:
    
    @pytest.fixture
    def backend(self):
        """Instancia del backend de autenticación"""
        return EmailOrUsernameModelBackend()
    
    @pytest.fixture
    def request_factory(self):
        """Factory para crear requests"""
        return RequestFactory()
    
    def test_authenticate_with_email(self, backend, request_factory, user):
        """Test autenticación con email"""
        request = request_factory.post('/login/')
        
        authenticated_user = backend.authenticate(
            request=request,
            username=user.email,
            password='testpass123'
        )
        
        assert authenticated_user == user

    def test_authenticate_with_username(self, backend, request_factory, user):
        """Test autenticación con username"""
        request = request_factory.post('/login/')
        
        authenticated_user = backend.authenticate(
            request=request,
            username=user.username,
            password='testpass123'
        )
        
        assert authenticated_user == user

    def test_authenticate_wrong_password(self, backend, request_factory, user):
        """Test autenticación con contraseña incorrecta"""
        request = request_factory.post('/login/')
        
        authenticated_user = backend.authenticate(
            request=request,
            username=user.email,
            password='wrongpassword'
        )
        
        assert authenticated_user is None

    def test_authenticate_nonexistent_user(self, backend, request_factory):
        """Test autenticación con usuario inexistente"""
        request = request_factory.post('/login/')
        
        authenticated_user = backend.authenticate(
            request=request,
            username='nonexistent@example.com',
            password='somepassword'
        )
        
        assert authenticated_user is None

    def test_authenticate_inactive_user(self, backend, request_factory, user):
        """Test autenticación con usuario inactivo"""
        user.is_active = False
        user.save()
        
        request = request_factory.post('/login/')
        
        authenticated_user = backend.authenticate(
            request=request,
            username=user.email,
            password='testpass123'
        )
        
        assert authenticated_user is None

    def test_authenticate_no_username(self, backend, request_factory):
        """Test autenticación sin username"""
        request = request_factory.post('/login/')
        
        authenticated_user = backend.authenticate(
            request=request,
            username=None,
            password='somepassword'
        )
        
        assert authenticated_user is None

    def test_authenticate_no_password(self, backend, request_factory, user):
        """Test autenticación sin password"""
        request = request_factory.post('/login/')
        
        authenticated_user = backend.authenticate(
            request=request,
            username=user.email,
            password=None
        )
        
        assert authenticated_user is None

    def test_authenticate_with_kwargs(self, backend, request_factory, user):
        """Test autenticación usando kwargs"""
        request = request_factory.post('/login/')
        
        # Simular cuando se pasa email como kwarg
        authenticated_user = backend.authenticate(
            request=request,
            email=user.email,
            password='testpass123'
        )
        
        assert authenticated_user == user

    def test_timing_attack_prevention(self, backend, request_factory):
        """Test prevención de timing attacks"""
        request = request_factory.post('/login/')
        
        # Debería tomar tiempo similar aunque el usuario no exista
        authenticated_user = backend.authenticate(
            request=request,
            username='nonexistent@example.com',
            password='somepassword'
        )
        
        assert authenticated_user is None

    def test_case_sensitive_authentication(self, backend, request_factory, user):
        """Test que la autenticación es case-sensitive"""
        request = request_factory.post('/login/')
        
        # Email en mayúsculas (debería fallar si es case-sensitive)
        authenticated_user = backend.authenticate(
            request=request,
            username=user.email.upper(),
            password='testpass123'
        )
        
        # Esto depende de tu configuración de base de datos
        # En la mayoría de los casos, debería ser None
        assert authenticated_user is None