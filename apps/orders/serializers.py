from rest_framework import serializers
from .models import Order
from user.models import UserAdress


class AddressSerializer(serializers.ModelSerializer):
    """Manzil serializeri"""
    class Meta:
        model = UserAdress
        fields = ['id', 'address', 'city', 'country', 'postal_code']
        read_only_fields = ['id']


class OrderSerializer(serializers.ModelSerializer):
    product_title = serializers.CharField(source="product.title", read_only=True)
    product_image = serializers.SerializerMethodField()
    buyer_username = serializers.CharField(source="buyer.username", read_only=True)
    buyer_full_name = serializers.CharField(source="buyer.get_full_name", read_only=True)
    seller_username = serializers.CharField(source="seller.username", read_only=True)
    buyer_address = serializers.SerializerMethodField()
    seller_shop_name = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "product",
            "product_title",
            "product_image",
            "buyer",
            "buyer_username",
            "buyer_full_name",
            "buyer_address",
            "seller",
            "seller_username",
            "seller_shop_name",
            "final_price",
            "status",
            "notes",
            "created_at",
            "updated_at"
        ]
        read_only_fields = [
            "id",
            "buyer",
            "seller",
            "final_price",
            "status",
            "created_at",
            "updated_at"
        ]

    def get_product_image(self, obj):
        try:
            img = obj.product.images.filter(is_main=True).first()
            if not img:
                img = obj.product.images.first()
            if img and img.image:
                return img.image.url
        except Exception:
            pass
        return None

    def get_buyer_address(self, obj):
        try:
            addr = getattr(obj.buyer, 'user_address', None)
            if addr:
                return {
                    'address': addr.address,
                    'city': addr.city,
                    'country': addr.country,
                    'postal_code': addr.postal_code,
                    'full': f"{addr.address}, {addr.city}, {addr.country}"
                }
        except Exception:
            pass
        return None

    def get_seller_shop_name(self, obj):
        try:
            if hasattr(obj.seller, 'seller_profile') and obj.seller.seller_profile:
                return obj.seller.seller_profile.shop_name
        except Exception:
            pass
        return None


class CreateOrderSerializer(serializers.Serializer):
    """Buyurtma yaratish uchun serializer"""
    product_id = serializers.IntegerField(required=True)
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    
    # Manzil ma'lumotlari (ixtiyoriy - yangi yoki mavjudni yangilash uchun)
    address = serializers.CharField(max_length=255, required=False)
    city = serializers.CharField(max_length=100, required=False)
    country = serializers.CharField(max_length=100, required=False)
    postal_code = serializers.CharField(max_length=20, required=False)
    use_saved_address = serializers.BooleanField(default=False, required=False)