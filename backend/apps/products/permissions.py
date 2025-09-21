# =============================================================================
# E-COMMERCE ARCHITECTURE: Custom Permissions
# =============================================================================
# STATUS: Completo - Listo para usar en futuras vistas
# PURPOSE: Permisos específicos para el sistema multi-vendor
# BUSINESS LOGIC: Controla acceso según roles y ownership
# NEXT STEPS: Usar estos permisos en ViewSets cuando se implementen
# =============================================================================

from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permiso personalizado para permitir solo a los propietarios editar objetos.
    """
    def has_object_permission(self, request, view, obj):
        # Permisos de lectura para cualquier solicitud
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Permisos de escritura solo para el propietario del objeto
        return obj.seller == request.user

class IsVendorOrReadOnly(permissions.BasePermission):
    """
    Permiso para vendors: pueden crear/editar, otros solo leer
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return (request.user.is_authenticated and 
                request.user.is_vendor and 
                request.user.can_sell_products())

class IsAdminOrVendorOwner(permissions.BasePermission):
    """
    Permiso para admin o vendor propietario del producto
    """
    def has_object_permission(self, request, view, obj):
        # Admin puede todo
        if request.user.is_authenticated and request.user.can_moderate_products():
            return True
        
        # Vendor puede editar solo sus productos
        if (request.user.is_authenticated and 
            request.user.is_vendor and 
            obj.seller == request.user):
            return True
        
        return False

class IsVerifiedVendor(permissions.BasePermission):
    """
    Solo vendors verificados pueden crear productos
    """
    def has_permission(self, request, view):
        return (request.user.is_authenticated and
                request.user.is_vendor and
                request.user.is_verified_vendor and
                request.user.is_active)

class IsAdminUser(permissions.BasePermission):
    """
    Solo administradores
    """
    def has_permission(self, request, view):
        return (request.user.is_authenticated and 
                request.user.can_moderate_products())