from rest_framework import serializers
from .models import Product, Category

class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(source='products.count', read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'product_count']
        read_only_fields = ['slug']

class ProductSerializer(serializers.ModelSerializer):
    # Para LEER (GET): Muestra el objeto completo de la categoría (nombre, slug, etc.)
    category = CategorySerializer(read_only=True) 

    # Para ESCRIBIR (POST/PUT): Solo necesitas enviar el ID de la categoría (ej: "category_id": 5)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True
    )

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'description', 'price', 'stock', 
                  'category', 'category_id', 'created_at', 'updated_at']
        read_only_fields = ['slug', 'created_at', 'updated_at']