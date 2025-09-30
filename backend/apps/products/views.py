from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg
from django.utils import timezone

from .models import Product, ProductImage, Category, Brand
from apps.users.models import User
from .serializers import (
    # Customer serializers
    ProductSerializer,
    ProductDetailSerializer,
    CategorySerializer,
    BrandSerializer,
    
    # Vendor serializers  
    VendorProductListSerializer,
    VendorProductCreateUpdateSerializer,
    VendorProductDetailSerializer,
    ProductImageSerializer,
    
    # Admin serializers
    AdminProductListSerializer
)
from .permissions import IsVendorOrReadOnly, IsOwnerOrReadOnly

# Import user serializers for admin endpoints
from apps.users.serializers import VendorProfileSerializer, AdminUserListSerializer

class ProductPagination(PageNumberPagination):
    """Paginacion personalizada para productos"""
    page_size = 12 #productos por pagina
    page_size_query_param = 'page_size' # parametro que cambia el tamano de la pagina
    max_page_size = 50 # maximo tamano de pagina

class AdminProductPagination(PageNumberPagination):
    """Paginacion personalizada para admin"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

# =============================================================================
# CUSTOMER ENDPOINTS - APIs Públicas
# =============================================================================
# ¿POR QUÉ ESTOS ENDPOINTS?
# - Permiten a cualquier usuario navegar el catálogo sin autenticación
# - Solo muestran productos activos de vendors verificados
# - Ocultan información sensible de moderación
# - Optimizados con select_related/prefetch_related para performance

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def public_list_products(request):
    """
    Lista pública de productos activos
    """
    # Base queryset: solo productos activos de vendors verificados
    queryset = Product.objects.filter(
        status='active',
        seller__is_verified_vendor=True,
        seller__is_active=True
    ).select_related(
        'category', 'brand', 'seller'
    ).prefetch_related('images')
    
    # FILTROS
    category_id = request.GET.get('category')
    if category_id:
        queryset = queryset.filter(category_id=category_id)
    
    brand_id = request.GET.get('brand')
    if brand_id:
        queryset = queryset.filter(brand_id=brand_id)
    
    # Filtro de rango de precios
    min_price = request.GET.get('min_price')
    if min_price:
        try:
            queryset = queryset.filter(price__gte=float(min_price))
        except ValueError:
            pass
    
    max_price = request.GET.get('max_price')
    if max_price:
        try:
            queryset = queryset.filter(price__lte=float(max_price))
        except ValueError:
            pass
    
    # Búsqueda de texto
    search = request.GET.get('search')
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) | 
            Q(description__icontains=search) |
            Q(category__name__icontains=search) |
            Q(brand__name__icontains=search)
        )
    
    # ORDENAMIENTO
    ordering = request.GET.get('ordering', '-created_at')
    valid_orderings = {
        'price': 'price',
        '-price': '-price',
        'created_at': 'created_at',
        '-created_at': '-created_at',
        'sales': '-sales_count',  # Más vendidos
        'views': '-views_count',  # Más vistos
        'name': 'name',
        '-name': '-name'
    }
    
    if ordering in valid_orderings:
        queryset = queryset.order_by(valid_orderings[ordering])
    else:
        queryset = queryset.order_by('-created_at')
    
    # Paginación
    paginator = ProductPagination()
    paginated_products = paginator.paginate_queryset(queryset, request)
    
    serializer = ProductSerializer(paginated_products, many=True)
    
    return paginator.get_paginated_response({
        'products': serializer.data,
        'total_count': queryset.count()
    })

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def public_product_detail(request, slug):
    """
    Detalle público de producto por slug
    
    BUSINESS LOGIC:
    - Solo productos activos de vendors verificados
    - Incrementa views_count automáticamente
    - Muestra todas las imágenes e información del seller
    - Incluye información de categoría y marca
    """
    product = get_object_or_404(
        Product.objects.select_related(
            'category', 'brand', 'seller'
        ).prefetch_related('images'),
        slug=slug,
        status='active',
        seller__is_verified_vendor=True,
        seller__is_active=True
    )
    product.increment_views() # Incrementar contador de vistas
    serializer = ProductDetailSerializer(product)

    return Response({ 'product': serializer.data})

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def public_category_list(request):
    """Lista pública de categorías activas"""
    categories = Category.objects.filter(is_active=True).annotate(
        active_product_count=Count('products', filter=Q(
            products__status='active',
            products__seller__is_verified_vendor=True,
            products__seller__is_active=True 
        ))
    ).order_by('name')

    serializer = CategorySerializer(categories, many=True)
    return Response({
        'categories': serializer.data,
        'total_count': categories.count()
    })

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def public_brand_list(request):
    """Lista pública de marcas activas"""
    brand = Brand.objects.filter(is_active=True).annotate(
        active_product_count=Count('products', filter=Q(
            products__status='active',
            products__seller__is_verified_vendor=True,
            products__seller__is_active=True 
        ))
    ).order_by('name')

    serializer = BrandSerializer(brand, many=True)
    return Response({
        'brands': serializer.data,
        'total_count': brand.count()
    })

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def public_products_search (request):
    """
    Busqueda pública de productos (similar a public_list_products)

    Este endpoint duplica funcionalidad de public_product_list pero
    con énfasis en búsqueda de texto. Podría consolidarse en producción.
    """
    # Reutilizar la lógica de public_list_products
    return public_list_products(request)

# =============================================================================
# 1. POST /api/vendor/products/ - Crear producto
# =============================================================================
# ¿POR QUÉ ESTE ENDPOINT PRIMERO?
# - Es el punto de entrada: sin productos no hay dashboard
# - Establece la relación producto-vendor desde el inicio
# - Define el estado inicial (draft) del workflow

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsVendorOrReadOnly])
def vendor_create_product(request):
    """
    Crear nuevo producto como vendor

    BUSINESS LOGIC:
    - Solo vendors verificados pueden crear productos
    - Producto inicia en estado 'draft'
    - Se asigna automáticamente al vendor autenticado
    - Validaciones de negocio: precio > 0, stock >= 0
    """
    # verificar que el usuario es un vendor verificado
    if not (request.user.is_vendor and request.user.is_verified_vendor):
        return Response(
            {"error": "Only verified vendors can create products."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # serializer para crear/actualizar producto
    serializer = VendorProductCreateUpdateSerializer(data=request.data) 
    
    #verificar si los datos son validos
    if serializer.is_valid():
        product = serializer.save(
            seller=request.user, 
            status='draft' #estado inicial
        ) # asignar vendor y estado inicial

        # retornar datos del producto creado
        detail_serializer = VendorProductDetailSerializer(product)
        return Response({
            "message": "Product created successfully.",
            "product": detail_serializer.data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# =============================================================================
# 2. GET /api/vendor/products/ - Lista MIS productos
# =============================================================================
# ¿POR QUÉ ESTE ENDPOINT SEGUNDO?
# - Permite verificar inmediatamente que el producto se creó
# - Muestra el dashboard del vendor
# - Incluye paginación y filtros básicos para escalar

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsVendorOrReadOnly])
def vendor_list_products(request):
    """
    Lista de productos del vendor autenticado
    
    BUSINESS LOGIC:
    - Solo ve SUS productos (filtro automático por seller)
    - Puede filtrar por estado, categoría, búsqueda
    - Incluye métricas básicas (views, sales)
    - Paginado para performance
    """
    # Filtros: solo productos del vendedor autenticado
    queryset = Product.objects.filter(seller=request.user)
    
    # Verificar que el usuario es vendor antes de continuar
    if not request.user.is_vendor:
        return Response(
            {"error": "Only vendors can access this endpoint."},
            status=status.HTTP_403_FORBIDDEN
        )

    # Filtreos opcionales via query params
    status_filter = request.GET.get('status')
    category_id = request.GET.get('category')
    search = request.GET.get('search')

    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if category_id:
        queryset = queryset.filter(category_id=category_id)
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) | 
            Q(description__icontains=search)
        )
    
    #ordenamiento por mas reciente
    queryset = queryset.select_related('category', 'brand').order_by('-created_at')

    # paginacion
    paginator = ProductPagination()
    paginated_products = paginator.paginate_queryset(queryset, request)

    serializer = VendorProductListSerializer(paginated_products, many=True)

    # Estadísticas del vendedor (optimizado para evitar múltiples consultas)
    # Usamos el queryset base para las estadísticas, no el paginado
    base_queryset = Product.objects.filter(seller=request.user)
    stats = {
        'total_products': base_queryset.count(),
        'draft_products': base_queryset.filter(status='draft').count(),
        'pending_products': base_queryset.filter(status='pending').count(), 
        'active_products': base_queryset.filter(status='active').count(),
        'rejected_products': base_queryset.filter(status='rejected').count(),
        'inactive_products': base_queryset.filter(status='inactive').count(),
    }
    
    # Agregar estadísticas de views y sales usando agregación
    from django.db.models import Sum
    totals = base_queryset.aggregate(
        total_views=Sum('views_count'),
        total_sales=Sum('sales_count')
    )
    stats.update({
        'total_views': totals['total_views'] or 0,
        'total_sales': totals['total_sales'] or 0,
    })
    return paginator.get_paginated_response({
        'products': serializer.data,
        'stats': stats
    })

# =============================================================================
# 3. GET /api/vendor/products/{id} - Ver MI producto
# =============================================================================
# ¿POR QUÉ ESTE ENDPOINT TERCERO?
# - Permite ver detalles completos de un producto específico
# - Incluye campos de moderación (approved_at, rejection_reason)
# - Muestra todas las imágenes asociadas
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsOwnerOrReadOnly])
def get_product_detail(request, pk):
    """
    Detalle de producto específico del vendor
    
    BUSINESS LOGIC:
    - Solo puede ver SUS propios productos
    - Muestra información completa incluyendo estado de moderación
    - Incluye todas las imágenes del producto
    """
    # Verificar que el usuario es vendor
    if not request.user.is_vendor:
        return Response(
            {"error": "Only vendors can access this endpoint."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # get_object_or_404 + filtro por vendedor = seguridad automática
    product = get_object_or_404(
        Product.objects.select_related('category', 'brand', 'approved_by').prefetch_related('images'),
        pk=pk, seller=request.user
    )
    
    # Usar el serializer específico para el detalle del vendor
    serializer = VendorProductDetailSerializer(product)
    return Response({
        "product": serializer.data
    })

# =============================================================================
# 4. PUT /api/vendor/products/{id} - Editar MI producto
# =============================================================================
# ¿POR QUÉ ESTE ENDPOINT CUARTO?
# - Permite correcciones después de crear el producto
# - Maneja lógica de estados: puede editar solo si está en draft/rejected
# - Resetea el estado de moderación si es necesario
@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated, IsOwnerOrReadOnly])
def update_product(request, pk):
    """
    Actualizar producto del vendor
    
    BUSINESS LOGIC:
    - Solo puede editar productos en estado 'draft' o 'rejected'
    - Si edita producto 'rejected', vuelve a 'draft' para nueva revisión
    - No puede cambiar seller ni campos de moderación
    """
    # Verificar que el usuario es vendor
    if not request.user.is_vendor:
        return Response(
            {"error": "Only vendors can access this endpoint."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    product = get_object_or_404(Product, pk=pk, seller=request.user)

    # verificar si se puede editar según el estado
    if product.status not in ['draft', 'rejected']:
        return Response(
            {"error": f"You can only edit products in 'draft' or 'rejected' status. Current status: {product.status}."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # determinar si la actualización es parcial o completa PUT vs PATCH
    partial = request.method == 'PATCH'
    serializer = VendorProductCreateUpdateSerializer(product, data=request.data, partial=partial)

    if serializer.is_valid():
        # Guardar los cambios
        updated_product = serializer.save()
        
        # Si el producto estaba rechazado y se actualiza, volver a draft para nueva revisión
        if product.status == 'rejected':
            updated_product.status = 'draft'
            updated_product.rejection_reason = ''  # Limpiar razón de rechazo
            updated_product.save(update_fields=['status', 'rejection_reason'])
        
        # Retornar producto actualizado
        detail_serializer = VendorProductDetailSerializer(updated_product)
        
        return Response({
            'message': 'Product updated successfully',
            'product': detail_serializer.data
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# =============================================================================
# 5. POST /api/vendor/products/{id}/images/ - Agregar imágenes
# =============================================================================
# ¿POR QUÉ ESTE ENDPOINT QUINTO?
# - Los productos necesitan imágenes para ser atractivos
# - Maneja la lógica de imagen primaria
# - Permite múltiples imágenes por product
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsOwnerOrReadOnly])
def add_product_image(request, pk):
    """
    Agregar imagen a producto del vendor
    
    BUSINESS LOGIC:
    - Solo puede agregar imágenes a SUS productos
    - Si es la primera imagen, se marca como primaria automáticamente
    - Valida formato y URL de imagen
    """
    # Verificar que el usuario es vendor
    if not request.user.is_vendor:
        return Response(
            {"error": "Only vendors can access this endpoint."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    product = get_object_or_404(Product, pk=pk, seller=request.user)

    # Preparar datos para la imagen
    image_data = request.data.copy()
    image_data['product'] = product.pk

    # Si es la primera imagen, marcarla como primaria automáticamente
    if not product.images.exists():
        image_data['is_primary'] = True

    serializer = ProductImageSerializer(data=image_data)

    if serializer.is_valid():
        image = serializer.save()

        return Response({
            "message": "Image added successfully.",
            "image": ProductImageSerializer(image).data
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# =============================================================================
# ENDPOINTS AUXILIARES - Gestión de imágenes
# =============================================================================
@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated, IsOwnerOrReadOnly])
def delete_product_image(request, product_pk, image_pk):
    """Eliminar imagen del producto"""
    # Verificar que el usuario es vendor
    if not request.user.is_vendor:
        return Response(
            {"error": "Only vendors can access this endpoint."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    product = get_object_or_404(Product, pk=product_pk, seller=request.user)
    image = get_object_or_404(ProductImage, pk=image_pk, product=product)

    was_primary = image.is_primary
    image.delete()

    # Si era primaria, asignar otra como primaria
    if was_primary:
        first_remaining = product.images.first()
        if first_remaining:
            first_remaining.is_primary = True
            first_remaining.save()
    
    return Response({"message": "Image deleted successfully."}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsOwnerOrReadOnly])
def set_primary_product_image(request, product_pk, image_pk):
    """Establecer imagen primaria del producto"""
    # Verificar que el usuario es vendor
    if not request.user.is_vendor:
        return Response(
            {"error": "Only vendors can access this endpoint."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    product = get_object_or_404(Product, pk=product_pk, seller=request.user)
    image = get_object_or_404(ProductImage, pk=image_pk, product=product)

    # Desmarcar cualquier imagen primaria existente
    product.images.update(is_primary=False)

    # Marcar la imagen seleccionada como primaria
    image.is_primary = True
    image.save()

    return Response({"message": "Image set as primary successfully."}, status=status.HTTP_200_OK)

# =============================================================================
# ENDPOINT PARA CAMBIAR ESTADO - Solo draft -> pending
# =============================================================================
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsOwnerOrReadOnly])
def submit_product_for_approval(request, pk):
    """
    Enviar producto para aprobación (draft -> pending)
    
    BUSINESS LOGIC:
    - Solo productos en 'draft' pueden enviarse para aprobación
    - Requiere al menos una imagen
    - Cambia estado a 'pending' para moderación admin
    """
    # Verificar que el usuario es vendor
    if not request.user.is_vendor:
        return Response(
            {"error": "Only vendors can access this endpoint."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    product = get_object_or_404(Product, pk=pk, seller=request.user)

    if product.status != 'draft':
        return Response(
            {"error": "Only products in 'draft' status can be submitted for approval."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validaciones antes de enviar para aprobación
    errors = []
    if not product.images.exists():
        errors.append("At least one product image is required.")
    if not product.description.strip():
        errors.append("Product description cannot be empty.")
    if product.price <= 0:
        errors.append("Product price must be greater than zero.")
    if product.stock < 0:
        errors.append("Product stock cannot be negative.")
    
    if errors:
        return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)
    
    # Cambiar status a pending
    product.status = 'pending'
    product.save(update_fields=['status'])

    return Response({
        "message": "Product submitted for approval successfully.", 
        "product": VendorProductDetailSerializer(product).data
    }, status=status.HTTP_200_OK)

# =============================================================================
# ADMIN ENDPOINTS - Moderación y Gestión
# =============================================================================
# ¿POR QUÉ ESTOS ENDPOINTS?
# - Permiten a admins moderar productos y vendors
# - Workflow completo: aprobar/rechazar con trazabilidad
# - Gestión de vendors: verificación y desactivación
# - Dashboard con estadísticas para toma de decisiones

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, permissions.IsAdminUser])
def admin_product_list(request):
    """
    Lista TODOS los productos para moderación admin
    
    BUSINESS LOGIC:
    - Admin ve TODOS los productos sin restricción
    - Filtros: estado, vendedor, categoría, búsqueda
    - Incluye información del seller y estado de moderación
    - Paginación más grande (20 items)
    
    Query Params:
    - status: draft, pending, active, rejected, inactive
    - seller: ID del vendedor
    - category: ID de categoría
    - search: Búsqueda en nombre/descripción
    """
    # Admin ve TODOS los productos
    queryset = Product.objects.all().select_related(
        'category', 'brand', 'seller', 'approved_by'
    ).prefetch_related('images')
    
    # FILTROS
    status_filter = request.GET.get('status')
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    seller_id = request.GET.get('seller')
    if seller_id:
        queryset = queryset.filter(seller_id=seller_id)
    
    category_id = request.GET.get('category')
    if category_id:
        queryset = queryset.filter(category_id=category_id)
    
    search = request.GET.get('search')
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) | 
            Q(description__icontains=search) |
            Q(seller__username__icontains=search) |
            Q(seller__store_name__icontains=search)
        )
    
    # Ordenamiento por defecto: pending primero, luego por fecha
    queryset = queryset.order_by(
        '-status',  # pending aparecen primero
        '-created_at'
    )
    
    # Paginación admin (más items)
    paginator = AdminProductPagination()
    paginated_products = paginator.paginate_queryset(queryset, request)
    
    serializer = AdminProductListSerializer(paginated_products, many=True)
    
    # Estadísticas globales
    stats = {
        'total_products': Product.objects.count(),
        'pending_products': Product.objects.filter(status='pending').count(),
        'active_products': Product.objects.filter(status='active').count(),
        'rejected_products': Product.objects.filter(status='rejected').count(),
        'draft_products': Product.objects.filter(status='draft').count(),
    }
    
    return paginator.get_paginated_response({
        'products': serializer.data,
        'stats': stats
    })

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, permissions.IsAdminUser])
def admin_approve_product(request, pk):
    """
    Aprobar producto (pending → active)
    
    BUSINESS LOGIC:
    - Solo productos en 'pending' pueden aprobarse
    - Registra quién y cuándo aprobó (trazabilidad)
    - Limpia rejection_reason si existía
    - Producto queda visible públicamente
    """
    product = get_object_or_404(
        Product.objects.select_related('seller'),
        pk=pk
    )
    
    if product.status != 'pending':
        return Response(
            {"error": f"Only products with 'pending' status can be approved. Current status: {product.status}"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Aprobar producto
    product.status = 'active'
    product.approved_by = request.user
    product.approved_at = timezone.now()
    product.rejection_reason = ''
    product.save(update_fields=['status', 'approved_by', 'approved_at', 'rejection_reason'])
    
    serializer = VendorProductDetailSerializer(product)
    
    return Response({
        'message': 'Product approved successfully',
        'product': serializer.data
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, permissions.IsAdminUser])
def admin_reject_product(request, pk):
    """
    Rechazar producto (pending → rejected)
    
    BUSINESS LOGIC:
    - Solo productos en 'pending' pueden rechazarse
    - Razón de rechazo es OBLIGATORIA
    - Registra quién rechazó (trazabilidad)
    - Vendor puede editar y reenviar
    
    Body:
    - rejection_reason: string (obligatorio)
    """
    product = get_object_or_404(
        Product.objects.select_related('seller'),
        pk=pk
    )
    
    if product.status != 'pending':
        return Response(
            {"error": f"Only products with 'pending' status can be rejected. Current status: {product.status}"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validar razón de rechazo
    rejection_reason = request.data.get('rejection_reason', '').strip()
    if not rejection_reason:
        return Response(
            {"error": "Rejection reason is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Rechazar producto
    product.status = 'rejected'
    product.rejection_reason = rejection_reason
    product.approved_by = request.user  # Registrar quién rechazó
    product.approved_at = timezone.now()
    product.save(update_fields=['status', 'rejection_reason', 'approved_by', 'approved_at'])
    
    serializer = VendorProductDetailSerializer(product)
    
    return Response({
        'message': 'Product rejected successfully',
        'product': serializer.data
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, permissions.IsAdminUser])
def admin_vendor_list(request):
    """
    Lista de vendors para gestión admin
    
    BUSINESS LOGIC:
    - Lista TODOS los usuarios con role='vendor'
    - Incluye métricas: total productos, productos activos
    - Muestra estado de verificación
    - Filtros: verificado, activo, búsqueda
    
    Query Params:
    - is_verified: true/false
    - is_active: true/false
    - search: Búsqueda en username/email/store_name
    """
    # Filtrar solo vendors
    queryset = User.objects.filter(role='vendor')
    
    # FILTROS
    is_verified = request.GET.get('is_verified')
    if is_verified is not None:
        is_verified_bool = is_verified.lower() == 'true'
        queryset = queryset.filter(is_verified_vendor=is_verified_bool)
    
    is_active = request.GET.get('is_active')
    if is_active is not None:
        is_active_bool = is_active.lower() == 'true'
        queryset = queryset.filter(is_active=is_active_bool)
    
    search = request.GET.get('search')
    if search:
        queryset = queryset.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(store_name__icontains=search)
        )
    
    # Ordenar por fecha de registro
    queryset = queryset.order_by('-created_at')
    
    # Paginación
    paginator = AdminProductPagination()
    paginated_vendors = paginator.paginate_queryset(queryset, request)
    
    serializer = AdminUserListSerializer(paginated_vendors, many=True)
    
    # Estadísticas de vendors
    stats = {
        'total_vendors': User.objects.filter(role='vendor').count(),
        'verified_vendors': User.objects.filter(role='vendor', is_verified_vendor=True).count(),
        'unverified_vendors': User.objects.filter(role='vendor', is_verified_vendor=False).count(),
        'active_vendors': User.objects.filter(role='vendor', is_active=True).count(),
    }
    
    return paginator.get_paginated_response({
        'vendors': serializer.data,
        'stats': stats
    })

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, permissions.IsAdminUser])
def admin_verify_vendor(request, pk):
    """
    Verificar vendor (permitir vender productos)
    
    BUSINESS LOGIC:
    - Solo usuarios con role='vendor' pueden verificarse
    - Vendor verificado puede crear y vender productos
    - Acción reversible (puede desverificarse)
    
    Body (opcional):
    - is_verified: boolean (default: true)
    """
    vendor = get_object_or_404(User, pk=pk, role='vendor')
    
    # Por defecto verificar, pero permitir desverificar
    is_verified = request.data.get('is_verified', True)
    
    vendor.is_verified_vendor = is_verified
    vendor.save(update_fields=['is_verified_vendor'])
    
    action = 'verified' if is_verified else 'unverified'
    
    serializer = VendorProfileSerializer(vendor)
    
    return Response({
        'message': f'Vendor {action} successfully',
        'vendor': serializer.data
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, permissions.IsAdminUser])
def admin_toggle_vendor_status(request, pk):
    """
    Activar/Desactivar vendor
    
    BUSINESS LOGIC:
    - Desactivar vendor oculta todos sus productos
    - Vendor desactivado no puede iniciar sesión
    - Acción reversible
    
    Body (opcional):
    - is_active: boolean (default: toggle actual)
    """
    vendor = get_object_or_404(User, pk=pk, role='vendor')
    
    # Por defecto toggle, pero permitir especificar
    is_active = request.data.get('is_active')
    if is_active is None:
        is_active = not vendor.is_active
    
    vendor.is_active = is_active
    vendor.save(update_fields=['is_active'])
    
    action = 'activated' if is_active else 'deactivated'
    
    serializer = VendorProfileSerializer(vendor)
    
    return Response({
        'message': f'Vendor {action} successfully',
        'vendor': serializer.data
    }, status=status.HTTP_200_OK)