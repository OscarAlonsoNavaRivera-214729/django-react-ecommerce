# backend/users/test_views.py
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

@pytest.mark.django_db
class TestUserRegistrationView:
    
    def test_register_success(self, api_client, user_data):
        """Test registro exitoso"""
        url = reverse('user-register')
        data = user_data.copy()
        data['password_confirm'] = data['password']
        
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'user' in response.data
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert response.data['message'] == 'User registered successfully'
        
        # Verificar que el usuario fue creado en la base de datos
        assert User.objects.filter(email=data['email']).exists()

    def test_register_password_mismatch(self, api_client, user_data):
        """Test registro con contraseñas que no coinciden"""
        url = reverse('user-register')
        data = user_data.copy()
        data['password_confirm'] = 'differentpassword'
        
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data

    def test_register_duplicate_email(self, api_client, user_data, user):
        """Test registro con email duplicado"""
        url = reverse('user-register')
        data = user_data.copy()
        data['username'] = 'differentuser'
        data['password_confirm'] = data['password']
        
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data

    def test_register_missing_fields(self, api_client):
        """Test registro con campos faltantes"""
        url = reverse('user-register')
        data = {
            'email': 'test@example.com'
            # Falta username, password, etc.
        }
        
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
class TestUserLoginView:
    
    def test_login_with_email_success(self, api_client, user):
        """Test login exitoso con email"""
        url = reverse('user-login')
        data = {
            'email': user.email,
            'password': 'testpass123'
        }
        
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'user' in response.data
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert response.data['message'] == 'Login exitoso'

    def test_login_with_username_success(self, api_client, user):
        """Test login exitoso con username"""
        url = reverse('user-login')
        data = {
            'username': user.username,
            'password': 'testpass123'
        }
        
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK

    def test_login_with_login_field_success(self, api_client, user):
        """Test login exitoso usando campo 'login'"""
        url = reverse('user-login')
        data = {
            'login': user.email,
            'password': 'testpass123'
        }
        
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK

    def test_login_invalid_credentials(self, api_client, user):
        """Test login con credenciales inválidas"""
        url = reverse('user-login')
        data = {
            'email': user.email,
            'password': 'wrongpassword'
        }
        
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'error' in response.data

    def test_login_inactive_user(self, api_client, user):
        """Test login con usuario inactivo"""
        user.is_active = False
        user.save()
        
        url = reverse('user-login')
        data = {
            'email': user.email,
            'password': 'testpass123'
        }
        
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_missing_fields(self, api_client):
        """Test login con campos faltantes"""
        url = reverse('user-login')
        data = {
            'password': 'testpass123'
            # Falta campo de identificación
        }
        
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
class TestUserProfileView:
    
    def test_get_profile_authenticated(self, authenticated_client, user):
        """Test obtener perfil autenticado"""
        url = reverse('user-profile')
        
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'user' in response.data
        assert response.data['user']['email'] == user.email

    def test_get_profile_unauthenticated(self, api_client):
        """Test obtener perfil sin autenticación"""
        url = reverse('user-profile')
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
class TestUpdateProfileView:
    
    def test_update_profile_success(self, authenticated_client, user):
        """Test actualización exitosa del perfil"""
        url = reverse('user-profile-update')
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone': '9876543210'
        }
        
        response = authenticated_client.put(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'Perfil actualizado exitosamente'
        
        # Verificar que los cambios se guardaron
        user.refresh_from_db()
        assert user.first_name == 'Updated'
        assert user.last_name == 'Name'
        assert user.phone == '9876543210'

    def test_partial_update_profile(self, authenticated_client, user):
        """Test actualización parcial del perfil"""
        url = reverse('user-profile-update')
        data = {
            'first_name': 'PartialUpdate'
        }
        
        response = authenticated_client.patch(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        
        user.refresh_from_db()
        assert user.first_name == 'PartialUpdate'

    def test_update_profile_unauthenticated(self, api_client):
        """Test actualización sin autenticación"""
        url = reverse('user-profile-update')
        data = {'first_name': 'Should Fail'}
        
        response = api_client.put(url, data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_readonly_fields(self, authenticated_client, user):
        """Test que no se pueden actualizar campos read-only"""
        original_id = user.id
        original_role = user.role
        
        url = reverse('user-profile-update')
        data = {
            'id': 999,
            'role': 'admin',
            'first_name': 'Updated'
        }
        
        response = authenticated_client.put(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        
        user.refresh_from_db()
        assert user.id == original_id
        assert user.role == original_role
        assert user.first_name == 'Updated'

@pytest.mark.django_db
class TestLogoutView:
    
    def test_logout_success(self, authenticated_client, user):
        """Test logout exitoso"""
        refresh = RefreshToken.for_user(user)
        
        url = reverse('user-logout')
        data = {'refresh': str(refresh)}
        
        response = authenticated_client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'Successfully logged out'

    def test_logout_invalid_token(self, authenticated_client):
        """Test logout con token inválido"""
        url = reverse('user-logout')
        data = {'refresh': 'invalid_token'}
        
        response = authenticated_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

    def test_logout_missing_token(self, authenticated_client):
        """Test logout sin token"""
        url = reverse('user-logout')
        data = {}
        
        response = authenticated_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_logout_unauthenticated(self, api_client, user):
        """Test logout sin autenticación"""
        refresh = RefreshToken.for_user(user)
        
        url = reverse('user-logout')
        data = {'refresh': str(refresh)}
        
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED