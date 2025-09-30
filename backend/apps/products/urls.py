from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# =============================================================================
# E-COMMERCE ARCHITECTURE: Products URL Structure
# =============================================================================
# STATUS: URLs implementadas para vendor endpoints
# PURPOSE: Estructura organizacional para endpoints por audiencia
# BUSINESS LOGIC: Rutas separadas por rol (customer, vendor, admin)
# NEXT STEPS: Implementar customer y admin endpoints
# =============================================================================

# Router para ViewSets (cuando se implementen)
router = DefaultRouter()
# router.register(r'', ProductViewSet, basename='product')  # Futuro
# router.register(r'categories', CategoryViewSet, basename='category')  # Futuro

urlpatterns = [
    # =============================================================================
    # VENDOR ENDPOINTS - Gestión completa de productos por vendors
    # =============================================================================
    
    # Gestión básica de productos
    path('vendor/', views.vendor_list_products, name='vendor-product-list'),           # GET: Lista productos del vendor
    path('vendor/create/', views.vendor_create_product, name='vendor-product-create'), # POST: Crear nuevo producto
    path('vendor/<int:pk>/', views.get_product_detail, name='vendor-product-detail'),  # GET: Detalle de producto
    path('vendor/<int:pk>/update/', views.update_product, name='vendor-product-update'), # PUT/PATCH: Actualizar producto
    
    # Gestión de imágenes
    path('vendor/<int:pk>/images/', views.add_product_image, name='vendor-product-add-image'),                    # POST: Agregar imagen
    path('vendor/<int:product_pk>/images/<int:image_pk>/delete/', views.delete_product_image, name='vendor-product-delete-image'),           # DELETE: Eliminar imagen
    path('vendor/<int:product_pk>/images/<int:image_pk>/set-primary/', views.set_primary_product_image, name='vendor-product-set-primary'),  # POST: Establecer imagen primaria
    
    # Workflow de estados
    path('vendor/<int:pk>/submit/', views.submit_product_for_approval, name='vendor-product-submit'),             # POST: Enviar para aprobación (draft -> pending)
    
    # =============================================================================
    # CUSTOMER ENDPOINTS - APIs públicas
    # =============================================================================  
    path('', views.public_list_products, name='product-list'),                   # GET: Lista pública de productos
    path('categories/', views.public_category_list, name='category-list'),       # GET: Lista de categorías
    path('brands/', views.public_brand_list, name='brand-list'),                 # GET: Lista de marcas
    path('search/', views.public_products_search, name='product-search'),        # GET: Búsqueda de productos
    path('<slug:slug>/', views.public_product_detail, name='product-detail'),    # GET: Detalle de producto por slug
    
    # =============================================================================
    # ADMIN ENDPOINTS - Moderación y gestión (futuro)
    # =============================================================================
    # path('admin/', include('products.admin_urls')),  # Futuro
]

# Comentado hasta implementar las vistas correspondientes
# Por ahora, los endpoints de vendor están completamente implementados