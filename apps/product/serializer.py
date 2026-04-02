from rest_framework import serializers
from .models import (
    Product, ProductImage, Category, Favorite,
    Brand, Color,
    PhoneAttribute, TVAttribute, LaptopAttribute,
    ClothingAttribute, ShoesAttribute, ApplianceAttribute,
    AutoAttribute, FoodAttribute, FurnitureAttribute,
    BookAttribute, HobbyAttribute, OtherAttribute,
)


# ── Yordamchi serializerlar ──
class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["id", "name", "logo"]


class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ["id", "name", "hex_code"]


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'order', 'is_main', 'created_at']
        read_only_fields = ['id', 'created_at']


# ══════════════════════════════════════════════
#  ATRIBUT SERIALIZERLARI
# ══════════════════════════════════════════════

class PhoneAttributeSerializer(serializers.ModelSerializer):
    color = ColorSerializer(read_only=True)
    color_id = serializers.PrimaryKeyRelatedField(
        queryset=Color.objects.all(), source="color", write_only=True, required=False,
    )

    class Meta:
        model = PhoneAttribute
        fields = ["model_name", "color", "color_id", "storage_gb", "ram_gb",
                  "battery_mah", "screen_size", "os", "sim_count", "camera_mp"]


class TVAttributeSerializer(serializers.ModelSerializer):
    color = ColorSerializer(read_only=True)
    color_id = serializers.PrimaryKeyRelatedField(
        queryset=Color.objects.all(), source="color", write_only=True, required=False,
    )

    class Meta:
        model = TVAttribute
        fields = ["model_name", "color", "color_id", "screen_size", "resolution",
                  "is_smart", "refresh_rate", "warranty_months"]


class LaptopAttributeSerializer(serializers.ModelSerializer):
    color = ColorSerializer(read_only=True)
    color_id = serializers.PrimaryKeyRelatedField(
        queryset=Color.objects.all(), source="color", write_only=True, required=False,
    )

    class Meta:
        model = LaptopAttribute
        fields = ["model_name", "color", "color_id", "processor", "ram_gb", "storage_gb",
                  "storage_type", "screen_size", "battery_hours", "os", "warranty_months"]


class ClothingAttributeSerializer(serializers.ModelSerializer):
    color = ColorSerializer(read_only=True)
    color_id = serializers.PrimaryKeyRelatedField(
        queryset=Color.objects.all(), source="color", write_only=True, required=False,
    )
    available_sizes = serializers.ListField(
        child=serializers.CharField(), required=False, default=list,
    )

    class Meta:
        model = ClothingAttribute
        fields = ["available_sizes", "color", "color_id", "gender", "material", "season"]


class ShoesAttributeSerializer(serializers.ModelSerializer):
    color = ColorSerializer(read_only=True)
    color_id = serializers.PrimaryKeyRelatedField(
        queryset=Color.objects.all(), source="color", write_only=True, required=False,
    )
    available_sizes = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list,
    )

    class Meta:
        model = ShoesAttribute
        fields = ["available_sizes", "color", "color_id", "gender", "material", "season"]


class ApplianceAttributeSerializer(serializers.ModelSerializer):
    color = ColorSerializer(read_only=True)
    color_id = serializers.PrimaryKeyRelatedField(
        queryset=Color.objects.all(), source="color", write_only=True, required=False,
    )

    class Meta:
        model = ApplianceAttribute
        fields = ["model_name", "color", "color_id", "power_watt", "energy_class",
                  "warranty_months", "weight_kg", "dimensions"]


class AutoAttributeSerializer(serializers.ModelSerializer):
    color = ColorSerializer(read_only=True)
    color_id = serializers.PrimaryKeyRelatedField(
        queryset=Color.objects.all(), source="color", write_only=True, required=False,
    )

    class Meta:
        model = AutoAttribute
        fields = ["make", "model_name", "year", "color", "color_id", "fuel_type",
                  "transmission", "drive_type", "mileage_km", "engine_cc"]


class FoodAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodAttribute
        fields = ["expiry_date", "weight", "weight_unit", "is_organic",
                  "ingredients", "storage_info"]


class FurnitureAttributeSerializer(serializers.ModelSerializer):
    color = ColorSerializer(read_only=True)
    color_id = serializers.PrimaryKeyRelatedField(
        queryset=Color.objects.all(), source="color", write_only=True, required=False,
    )

    class Meta:
        model = FurnitureAttribute
        fields = ["material", "color", "color_id", "dimensions", "weight_kg", "warranty_months"]


class BookAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookAttribute
        fields = ["author", "publisher", "language", "pages", "isbn", "genre"]


class HobbyAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = HobbyAttribute
        fields = ["hobby_type", "age_min", "age_max", "material"]


class OtherAttributeSerializer(serializers.ModelSerializer):
    color = ColorSerializer(read_only=True)
    color_id = serializers.PrimaryKeyRelatedField(
        queryset=Color.objects.all(), source="color", write_only=True, required=False,
    )

    class Meta:
        model = OtherAttribute
        fields = ["material", "color", "color_id", "weight_kg", "warranty_months"]


# ══════════════════════════════════════════════
#  ASOSIY MAHSULOT SERIALIZERI
# ══════════════════════════════════════════════

# Kategoriya turi → (field_name, Model, Serializer)
ATTR_MAP = {
    "phone":     ("phone_attr",     PhoneAttribute,     PhoneAttributeSerializer),
    "tv":        ("tv_attr",        TVAttribute,        TVAttributeSerializer),
    "laptop":    ("laptop_attr",    LaptopAttribute,    LaptopAttributeSerializer),
    "clothing":  ("clothing_attr",  ClothingAttribute,  ClothingAttributeSerializer),
    "shoes":     ("shoes_attr",     ShoesAttribute,     ShoesAttributeSerializer),
    "appliance": ("appliance_attr", ApplianceAttribute, ApplianceAttributeSerializer),
    "auto":      ("auto_attr",      AutoAttribute,      AutoAttributeSerializer),
    "food":      ("food_attr",      FoodAttribute,      FoodAttributeSerializer),
    "furniture": ("furniture_attr", FurnitureAttribute, FurnitureAttributeSerializer),
    "book":      ("book_attr",      BookAttribute,      BookAttributeSerializer),
    "hobby":     ("hobby_attr",     HobbyAttribute,     HobbyAttributeSerializer),
    "other":     ("other_attr",     OtherAttribute,     OtherAttributeSerializer),
}

ALL_ATTR_FIELDS = [v[0] for v in ATTR_MAP.values()]


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    brand = BrandSerializer(read_only=True)
    brand_id = serializers.PrimaryKeyRelatedField(
        queryset=Brand.objects.all(), source="brand", write_only=True, required=False,
    )

    tax_amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True,
    )
    price_with_tax = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True,
    )

    # Barcha atributlar — faqat tegishli toifadagisi to'ldiriladi
    phone_attr = PhoneAttributeSerializer(required=False, allow_null=True)
    tv_attr = TVAttributeSerializer(required=False, allow_null=True)
    laptop_attr = LaptopAttributeSerializer(required=False, allow_null=True)
    clothing_attr = ClothingAttributeSerializer(required=False, allow_null=True)
    shoes_attr = ShoesAttributeSerializer(required=False, allow_null=True)
    appliance_attr = ApplianceAttributeSerializer(required=False, allow_null=True)
    auto_attr = AutoAttributeSerializer(required=False, allow_null=True)
    food_attr = FoodAttributeSerializer(required=False, allow_null=True)
    furniture_attr = FurnitureAttributeSerializer(required=False, allow_null=True)
    book_attr = BookAttributeSerializer(required=False, allow_null=True)
    hobby_attr = HobbyAttributeSerializer(required=False, allow_null=True)
    other_attr = OtherAttributeSerializer(required=False, allow_null=True)

    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = [
            'id', 'seller', 'view_count', 'favorite_count',
            'status', 'created_at', 'updated_at',
            'images', 'tax_amount', 'price_with_tax',
        ]

    def create(self, validated_data):
        attr_data_all = {}
        for field_name in ALL_ATTR_FIELDS:
            attr_data_all[field_name] = validated_data.pop(field_name, None)

        validated_data['seller'] = self.context['request'].user
        product = super().create(validated_data)

        # Tegishli atributni saqlash
        cat_type = product.category.category_type if product.category else None
        if cat_type and cat_type in ATTR_MAP:
            field_name, model_cls, _ = ATTR_MAP[cat_type]
            attr_data = attr_data_all.get(field_name)
            if attr_data:
                model_cls.objects.create(product=product, **attr_data)

        return product

    def update(self, instance, validated_data):
        attr_data_all = {}
        for field_name in ALL_ATTR_FIELDS:
            attr_data_all[field_name] = validated_data.pop(field_name, None)

        instance = super().update(instance, validated_data)

        cat_type = instance.category.category_type if instance.category else None
        if cat_type and cat_type in ATTR_MAP:
            field_name, model_cls, _ = ATTR_MAP[cat_type]
            attr_data = attr_data_all.get(field_name)
            if attr_data:
                model_cls.objects.update_or_create(
                    product=instance, defaults=attr_data,
                )

        return instance


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class FavoriteSerializer(serializers.ModelSerializer):
    product_detail = ProductSerializer(source="product", read_only=True)

    class Meta:
        model = Favorite
        fields = ['id', 'product', 'product_detail', 'created_at']
        read_only_fields = ['id', 'user', 'product', 'created_at']