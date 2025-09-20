from django.db import models
from django.utils.text import slugify
from django.conf import settings

# =============================================================================
# E-COMMERCE ARCHITECTURE: Product Management with Multi-Vendor Support
# =============================================================================
# STATUS: Completo
# PURPOSE: Sistema completo de productos con workflow de estados y multi-vendor
# BUSINESS LOGIC:
# - Products: draft → pending → active (workflow de moderación)
# - Vendors: Solo pueden crear, admin debe aprobar
# - Categories & Brands: Organizan productos
# - Images: Sistema flexible con imagen principal
# NEXT STEPS: Implementar sistema de reviews y ratings
# =============================================================================

#-----Category Model-----
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

#-----Product Model-----
class Product(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('pending', 'Pendiente Aprobación'),
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
        ('rejected', 'Rechazado'),
    ]
    
    # Información básica
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    brand = models.ForeignKey('Brand', related_name='products', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Sistema de vendedores/ownership
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        related_name='products_selling',
        on_delete=models.CASCADE,
        help_text="Usuario que vende este producto"
    )
    
    # Estado y moderación
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False)  # Solo admin puede marcar como destacado
    
    # Campos de moderación
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='products_approved',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        help_text="Admin que aprobó el producto"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Métricas
    views_count = models.PositiveIntegerField(default=0)
    sales_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'is_featured']),
            models.Index(fields=['seller', 'status']),
            models.Index(fields=['category', 'status']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"
    
    @property
    def is_available(self):
        """Producto disponible para compra"""
        return self.status == 'active' and self.stock > 0
    
    @property
    def can_be_purchased(self):
        """Alias para is_available"""
        return self.is_available
    
    def increment_views(self):
        """Incrementar contador de vistas"""
        self.views_count += 1
        self.save(update_fields=['views_count'])
    
    def decrement_stock(self, quantity=1):
        """Decrementar stock después de venta"""
        if self.stock >= quantity:
            self.stock -= quantity
            self.sales_count += quantity
            self.save(update_fields=['stock', 'sales_count'])
            return True
        return False
    
#-----Product Image Model-----
class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image_url = models.URLField()
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)  # Orden de las imágenes
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"
        ordering = ['-is_primary', 'order', 'created_at']

    def save(self, *args, **kwargs):
        # Solo una imagen puede ser primaria por producto
        if self.is_primary and self.product_id:
            # Exclude this instance (if it exists) to avoid unnecessary writes
            qs = ProductImage.objects.filter(product_id=self.product_id, is_primary=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            qs.update(is_primary=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Image for {self.product.name} ({'Primary' if self.is_primary else 'Secondary'})"
class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    logo_url = models.URLField(blank=True)
    website = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


