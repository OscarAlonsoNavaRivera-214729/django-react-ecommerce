from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from .models import User

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Custom authentication backend that allows users to authenticate using either their email or username.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)

        if username is None or password is None:
            return None
        try:
            #busca usuario por emial o por username
            user = User.objects.get(Q(email=username) | Q(username=username))
        except User.DoesNotExist:
            #crea un usuario en blanco para evitar timing attacks
            User().set_password(password)
            return None
        
        #verificar password y si el usuario esta activo
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None