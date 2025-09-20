from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import Product, ProductImage
from .serializers import (
    VendorProductListSerializer,
    VendorProductCreateUpdateSerializer,
    VendorProductDetailSerializer,
    ProductImageSerializer
)
from .permissions import IsVendorOrReadOnly, IsOwnerOrReadOnly

class ProductPagination(PageNumberPagination):
    """Paginacion personalizada para productos"""
    page_size = 12 #productos por pagina
    page_size_query_param = 'page_size' # parametro que cambia el tamano de la pagina
    max_page_size = 50 # maximo tamano de pagina

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
