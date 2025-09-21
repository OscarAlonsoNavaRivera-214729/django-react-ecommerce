from rest_framework import serializers
from .models import User

# =============================================================================
# E-COMMERCE ARCHITECTURE: User Authentication & Registration
# =============================================================================
# STATUS: Completo
# PURPOSE: Registro y autenticación base para todas las audiencias  
# BUSINESS LOGIC: Validación segura de passwords, campos únicos
# NEXT STEPS: Implementar registro específico para vendors
# =============================================================================

class UserRegistrationSerializer(serializers.ModelSerializer):
    # Campos para la validacion de contrasena
    password = serializers.CharField(write_only=True, required=True)
    password_confirm = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, default='customer')

    class Meta:
        model = User
        fields = ['email', 'username', 'first_name', 'last_name', 
                 'password', 'password_confirm', 'phone', 'address', 'role']
    
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

class VendorRegistrationSerializer(UserRegistrationSerializer):
    """Registro específico para vendors - incluye campos de tienda"""
    store_name = serializers.CharField(required=True)
    store_description = serializers.CharField(required=False, allow_blank=True)
    
    class Meta(UserRegistrationSerializer.Meta):
        fields = UserRegistrationSerializer.Meta.fields + ['store_name', 'store_description']
    
    def validate_store_name(self, value):
        if User.objects.filter(store_name=value, role='vendor').exists():
            raise serializers.ValidationError("Store name already exists")
        return value
    
    def create(self, validated_data):
        validated_data['role'] = 'vendor'  # Forzar rol vendor
        return super().create(validated_data)

class LoginSerializer(serializers.Serializer):
    """Serializer para login con email o username"""
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

# =============================================================================
# E-COMMERCE ARCHITECTURE: User Profile Serializers by Audience
# =============================================================================
# STATUS: Completo
# PURPOSE: Diferentes vistas de perfil según el rol del usuario
# BUSINESS LOGIC: Cada rol ve campos específicos a sus necesidades
# NEXT STEPS: Crear endpoints específicos que usen estos serializers
# =============================================================================

class CustomerProfileSerializer(serializers.ModelSerializer):
    """Perfil para clientes - campos básicos de compra"""
    full_name = serializers.ReadOnlyField()
    is_oauth_user = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'full_name',
                 'phone', 'address', 'avatar', 'is_oauth_user', 'created_at']
        read_only_fields = ['id', 'email', 'created_at']

class VendorProfileSerializer(serializers.ModelSerializer):
    """Perfil para vendors - incluye campos de tienda"""
    full_name = serializers.ReadOnlyField()
    display_name = serializers.ReadOnlyField()
    can_sell_products = serializers.ReadOnlyField()
    total_products = serializers.SerializerMethodField()
    active_products = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'full_name',
                 'phone', 'address', 'avatar', 'store_name', 'store_description',
                 'is_verified_vendor', 'display_name', 'can_sell_products',
                 'total_products', 'active_products', 'created_at']
        read_only_fields = ['id', 'email', 'is_verified_vendor', 'created_at']
    
    def get_total_products(self, obj):
        return obj.products_selling.count()
    
    def get_active_products(self, obj):
        return obj.products_selling.filter(status='active').count()

class AdminUserListSerializer(serializers.ModelSerializer):
    """Lista de usuarios para admin - resumen con métricas"""
    full_name = serializers.ReadOnlyField()
    display_name = serializers.ReadOnlyField()
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'full_name', 'display_name',
                 'role', 'is_verified_vendor', 'is_active', 'products_count', 'created_at']
    
    def get_products_count(self, obj):
        if obj.role == 'vendor':
            return obj.products_selling.count()
        return 0

class AdminUserDetailSerializer(serializers.ModelSerializer):
    """Detalle completo para admin - todos los campos"""
    full_name = serializers.ReadOnlyField()
    display_name = serializers.ReadOnlyField()
    can_sell_products = serializers.ReadOnlyField()
    can_moderate_products = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = '__all__'
        read_only_fields = ['id', 'password', 'last_login', 'date_joined', 'created_at']

class AdminVendorModerationSerializer(serializers.ModelSerializer):
    """Serializer para moderar vendors (verificar/desactivar)"""
    
    class Meta:
        model = User
        fields = ['is_verified_vendor', 'is_active']
    
    def validate(self, attrs):
        # Solo permitir moderar vendors
        if self.instance and self.instance.role != 'vendor':
            raise serializers.ValidationError("This endpoint is only for vendor accounts")
        return attrs

# =============================================================================
# E-COMMERCE ARCHITECTURE: General User Serializer
# =============================================================================
# STATUS: Completo  
# PURPOSE: Serializer legacy mantenido para compatibilidad
# BUSINESS LOGIC: Usar los específicos por audiencia en nuevos endpoints
# NEXT STEPS: Migrar endpoints existentes a usar serializers específicos
# =============================================================================

class UserSerializer(serializers.ModelSerializer):
    """Serializer general - mantener para compatibilidad"""
    full_name = serializers.ReadOnlyField()
    is_oauth_user = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'full_name',
                 'role', 'phone', 'address', 'avatar', 'provider', 'is_oauth_user', 'created_at']
        read_only_fields = ['id', 'role', 'provider', 'created_at']