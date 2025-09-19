from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Product, Category, ProductImage, Brand

User = get_user_model()

# =============================================================================
# E-COMMERCE ARCHITECTURE: Core Serializers
# =============================================================================
# STATUS: Completo
# PURPOSE: Serializers básicos reutilizables para todas las audiencias
# BUSINESS LOGIC: Componentes base para construir APIs específicas por rol
# NEXT STEPS: Implementar vistas que usen estos serializers por audiencia
# =============================================================================

class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(source='products.count', read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'is_active', 'product_count']
        read_only_fields = ['slug']
    
    def get_product_count(self, obj):
        return obj.products.filter(status='active').count()

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image_url', 'alt_text', 'is_primary', 'order']

class BrandSerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(source='products.count', read_only=True)
    
    class Meta:
        model = Brand
        fields = ['id', 'name', 'slug', 'description', 'logo_url', 'website', 'product_count']
        read_only_fields = ['slug']

class SellerInfoSerializer(serializers.ModelSerializer):
    """Información básica del vendedor para mostrar en productos"""
    class Meta:
        model = User
        fields = ['id', 'username', 'display_name', 'is_verified_vendor', 'store_description']

# =============================================================================
# E-COMMERCE ARCHITECTURE: Customer Audience Serializers
# =============================================================================
# STATUS: Completo
# PURPOSE: API para clientes - solo información necesaria para compra
# BUSINESS LOGIC: Oculta información sensible, muestra solo productos activos
# NEXT STEPS: Crear vistas de catálogo que usen estos serializers
# =============================================================================

class ProductSerializer(serializers.ModelSerializer):
    """Serializer para lista de productos (vista del cliente)"""
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    primary_image = serializers.SerializerMethodField()
    seller_info = SellerInfoSerializer(source='seller', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'stock',
            'category', 'brand', 'primary_image', 'seller_info', 'is_featured',
            'views_count', 'sales_count', 'created_at'
        ]

    def get_primary_image(self, obj):
        primary = obj.images.filter(is_primary=True).first()
        if primary:
            return ProductImageSerializer(primary).data
        return None

class ProductDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalle de producto (vista del cliente)"""
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    seller_info = SellerInfoSerializer(source='seller', read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'stock',
            'category', 'brand', 'images', 'seller_info', 'is_featured',
            'views_count', 'sales_count', 'created_at', 'updated_at'
        ]

# =============================================================================
# E-COMMERCE ARCHITECTURE: Vendor Audience Serializers  
# =============================================================================
# STATUS: Completo
# PURPOSE: API para vendedores - gestión de sus propios productos
# BUSINESS LOGIC: Solo pueden ver/editar sus productos, campos de workflow
# NEXT STEPS: Crear vistas de dashboard vendor con estos serializers
# =============================================================================

class VendorProductListSerializer(serializers.ModelSerializer):
    """Lista de productos del vendor - incluye estados y métricas"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    primary_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'price', 'stock', 'status',
            'category_name', 'brand_name', 'primary_image',
            'is_featured', 'views_count', 'sales_count',
            'created_at', 'updated_at'
        ]
    
    def get_primary_image(self, obj):
        primary = obj.images.filter(is_primary=True).first()
        return primary.image_url if primary else None

class VendorProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Crear/editar productos por vendors"""
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True), 
        source='category', 
        write_only=True
    )
    brand_id = serializers.PrimaryKeyRelatedField(
        queryset=Brand.objects.filter(is_active=True), 
        source='brand', 
        write_only=True,
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'price', 'stock', 
            'category_id', 'brand_id'
        ]
    
    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0")
        return value
    
    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError("Stock cannot be negative")
        return value

class VendorProductDetailSerializer(serializers.ModelSerializer):
    """Detalle completo para vendor - incluye campos de moderación"""
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    approved_by_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'stock',
            'category', 'brand', 'images', 'status', 'is_featured',
            'approved_by_info', 'approved_at', 'rejection_reason',
            'views_count', 'sales_count', 'created_at', 'updated_at'
        ]
    
    def get_approved_by_info(self, obj):
        if obj.approved_by:
            return {
                'id': obj.approved_by.id,
                'username': obj.approved_by.username,
                'full_name': obj.approved_by.full_name
            }
        return None

# =============================================================================
# E-COMMERCE ARCHITECTURE: Admin Audience Serializers
# =============================================================================
# STATUS: Completo  
# PURPOSE: API para admins - moderación y gestión completa
# BUSINESS LOGIC: Acceso total, campos de moderación, estadísticas avanzadas
# NEXT STEPS: Crear panel admin con filtros avanzados usando estos serializers
# =============================================================================

class AdminProductListSerializer(serializers.ModelSerializer):
    """Lista para admin - incluye seller y estado de moderación"""
    seller_info = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'price', 'stock', 'status',
            'seller_info', 'category_name', 'brand_name',
            'is_featured', 'views_count', 'sales_count',
            'created_at', 'approved_at'
        ]
    
    def get_seller_info(self, obj):
        return {
            'id': obj.seller.id,
            'username': obj.seller.username,
            'store_name': obj.seller.store_name,
            'is_verified_vendor': obj.seller.is_verified_vendor
        }

class AdminProductModerationSerializer(serializers.ModelSerializer):
    """Serializer para aprobar/rechazar productos"""
    
    class Meta:
        model = Product
        fields = ['status', 'rejection_reason', 'is_featured']
    
    def validate_status(self, value):
        if value == 'rejected' and not self.initial_data.get('rejection_reason'):
            raise serializers.ValidationError(
                "Rejection reason is required when rejecting a product"
            )
        return value
    
    def update(self, instance, validated_data):
        user = self.context['request'].user
        
        # Si se aprueba el producto
        if validated_data.get('status') == 'active':
            validated_data['approved_by'] = user
            validated_data['approved_at'] = timezone.now()
            validated_data['rejection_reason'] = ''  # Limpiar razón de rechazo
        
        return super().update(instance, validated_data)