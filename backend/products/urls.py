from django.urls import path, include
from rest_framework.routers import DefaultRouter

# =============================================================================
# E-COMMERCE ARCHITECTURE: Products URL Structure
# =============================================================================
# STATUS: Preparado para futuras vistas
# PURPOSE: Estructura organizacional para endpoints por audiencia
# BUSINESS LOGIC: Rutas separadas por rol (customer, vendor, admin)
# NEXT STEPS: Implementar ViewSets que usen los serializers por audiencia
# =============================================================================

# Router para ViewSets (cuando se implementen)
router = DefaultRouter()
# router.register(r'', ProductViewSet, basename='product')  # Futuro
# router.register(r'categories', CategoryViewSet, basename='category')  # Futuro

urlpatterns = [
    # APIs públicas (customer)
    # path('', include(router.urls)),  # Futuro: Lista de productos
    # path('categories/', views.CategoryListView.as_view(), name='category-list'),  # Futuro
    # path('<slug:slug>/', views.ProductDetailView.as_view(), name='product-detail'),  # Futuro
    
    # APIs para vendors  
    # path('vendor/', include('products.vendor_urls')),  # Futuro
    
    # APIs para admin
    # path('admin/', include('products.admin_urls')),  # Futuro
]

# Comentado hasta implementar las vistas correspondientes
# Por ahora, los serializers están listos y las URLs preparadas