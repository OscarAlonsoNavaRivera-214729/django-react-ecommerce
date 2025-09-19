# =============================================================================
# E-COMMERCE ARCHITECTURE: User Permissions
# =============================================================================
# STATUS: Completo - Listo para usar en futuras vistas
# PURPOSE: Permisos específicos para gestión de usuarios por rol
# BUSINESS LOGIC: Control granular de acceso a perfiles y datos de usuario
# NEXT STEPS: Usar en ViewSets de gestión de usuarios
# =============================================================================

from rest_framework import permissions

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Solo el propietario del perfil o un admin pueden acceder
    """
    def has_object_permission(self, request, view, obj):
        # Admin puede ver/editar cualquier perfil
        if request.user.is_authenticated and request.user.can_moderate_products():
            return True
        
        # Usuario puede ver/editar solo su perfil
        return obj == request.user

class IsAdminOrSelfRegister(permissions.BasePermission):
    """
    Admin puede crear cualquier usuario, otros solo pueden registrarse a sí mismos
    """
    def has_permission(self, request, view):
        # Para registro público
        if request.method == 'POST':
            return True
        
        # Para otras operaciones, debe estar autenticado
        return request.user.is_authenticated

class CanModerateVendors(permissions.BasePermission):
    """
    Solo admin puede moderar vendors (verificar/desactivar)
    """
    def has_permission(self, request, view):
        return (request.user.is_authenticated and 
                request.user.can_moderate_products())
    
    def has_object_permission(self, request, view, obj):
        # Solo se puede moderar vendors
        return obj.role == 'vendor'