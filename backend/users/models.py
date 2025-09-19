from django.db import models
from django.contrib.auth.models import AbstractUser

# =============================================================================
# E-COMMERCE ARCHITECTURE: Multi-Role User System
# =============================================================================
# STATUS: Completo
# PURPOSE: Sistema de usuarios con roles específicos para e-commerce
# BUSINESS LOGIC: 
# - Customers: Pueden comprar productos
# - Vendors: Pueden vender productos (requieren verificación)
# - Admins: Pueden moderar productos y usuarios
# NEXT STEPS: Implementar sistema de verificación automática para vendors
# =============================================================================

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('vendor','Vendor'),
        ('customer', 'Customer'),
    ]
    # Campos principales
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    
    # Campos para  integracion OAuth
    provider = models.CharField(max_length=50, blank=True, null=True)
    provider_id = models.CharField(max_length=100, blank=True, null=True)
    avatar = models.URLField(blank=True, null=True)

    # Campos específicos para vendedores
    store_name = models.CharField(max_length=200, blank=True, help_text="Nombre de la tienda (solo vendors)")
    store_description = models.TextField(blank=True, help_text="Descripción de la tienda")
    is_verified_vendor = models.BooleanField(default=False, help_text="Vendor verificado por admin")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Configuración de autenticación
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f'{self.email} ({self.get_role_display()})'
    
    @property
    def is_admin(self):
        return self.role == 'admin' or self.is_superuser
    
    @property
    def is_vendor(self):
        return self.role == 'vendor'
    
    @property
    def is_customer(self):
        return self.role == 'customer'
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def is_oauth_user(self):
        return bool(self.provider)
    @property
    def display_name(self):
        """Nombre para mostrar: store_name si es vendor, sino full_name"""
        if self.is_vendor and self.store_name:
            return self.store_name
        return self.full_name or self.username
    
    def can_sell_products(self):
        """Verifica si el usuario puede vender productos"""
        return self.is_vendor and self.is_active
    
    def can_moderate_products(self):
        """Verifica si puede moderar productos"""
        return self.is_admin and self.is_active