# =============================================================================
# E-COMMERCE ARCHITECTURE: Development Utilities
# =============================================================================
# STATUS: Opcional - Utilidades para desarrollo
# PURPOSE: Funciones helper para testing y desarrollo
# BUSINESS LOGIC: Facilita testing de la arquitectura multi-vendor
# NEXT STEPS: Usar en tests y comandos de management
# =============================================================================

from django.contrib.auth import get_user_model

User = get_user_model()

def create_test_users():
    """
    Crear usuarios de prueba para cada rol
    Útil para desarrollo y testing
    """
    
    # Admin user
    admin, created = User.objects.get_or_create(
        email='admin@ecommerce.com',
        defaults={
            'username': 'admin',
            'first_name': 'Admin',
            'last_name': 'User',
            'role': 'admin',
            'is_superuser': True,
            'is_staff': True,
        }
    )
    if created:
        admin.set_password('admin123')
        admin.save()
    
    # Verified vendor
    vendor, created = User.objects.get_or_create(
        email='vendor@ecommerce.com',
        defaults={
            'username': 'vendor1',
            'first_name': 'Vendor',
            'last_name': 'One',
            'role': 'vendor',
            'store_name': 'Tech Store',
            'store_description': 'Best electronics in town',
            'is_verified_vendor': True,
        }
    )
    if created:
        vendor.set_password('vendor123')
        vendor.save()
    
    # Customer
    customer, created = User.objects.get_or_create(
        email='customer@ecommerce.com',
        defaults={
            'username': 'customer1',
            'first_name': 'Customer',
            'last_name': 'One',
            'role': 'customer',
        }
    )
    if created:
        customer.set_password('customer123')
        customer.save()
    
    return admin, vendor, customer

def create_test_categories():
    """Crear categorías de prueba"""
    from products.models import Category
    
    categories_data = [
        {'name': 'Electronics', 'description': 'Electronic devices and gadgets'},
        {'name': 'Clothing', 'description': 'Fashion and apparel'},
        {'name': 'Books', 'description': 'Books and literature'},
        {'name': 'Home & Garden', 'description': 'Home improvement and gardening'},
    ]
    
    categories = []
    for cat_data in categories_data:
        category, created = Category.objects.get_or_create(
            name=cat_data['name'],
            defaults=cat_data
        )
        categories.append(category)
    
    return categories

def create_test_brands():
    """Crear marcas de prueba"""
    from products.models import Brand
    
    brands_data = [
        {'name': 'Apple', 'description': 'Think Different'},
        {'name': 'Samsung', 'description': 'Inspire the World'},
        {'name': 'Nike', 'description': 'Just Do It'},
        {'name': 'Adidas', 'description': 'Impossible is Nothing'},
    ]
    
    brands = []
    for brand_data in brands_data:
        brand, created = Brand.objects.get_or_create(
            name=brand_data['name'],
            defaults=brand_data
        )
        brands.append(brand)
    
    return brands