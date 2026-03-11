from rest_framework import serializers
from .models import Product, ProductImage, Category, Favorite

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'order', 'is_main', 'created_at']
        read_only_fields = ['id', 'created_at']

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = [
            'id',
            'seller',
            'view_count',
            'favorite_count',
            'status',
            'created_at',
            'updated_at',
            'images',
        ]
    def get_images(self, obj):
        images = obj.images.all().order_by('-is_main', 'order', 'id')
        return ProductImageSerializer(images, many=True).data
    def create(self, validated_data):
        validated_data['seller'] = self.context['request'].user
        return super().create(validated_data)
    
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"
        
class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ['id', 'product', 'created_at']
        read_only_fields = ['id', 'user', 'product', 'created_at']