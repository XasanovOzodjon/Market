from django.contrib import admin
from .models import (
    Product, ProductImage, Favorite, Category,
    Brand, Color,
    PhoneAttribute, TVAttribute, LaptopAttribute,
    ClothingAttribute, ShoesAttribute, ApplianceAttribute,
    AutoAttribute, FoodAttribute, FurnitureAttribute,
    BookAttribute, HobbyAttribute, OtherAttribute,
    PendingProductEdit,
)


# ── Inline modellar ──
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class PhoneAttributeInline(admin.StackedInline):
    model = PhoneAttribute
    extra = 0
    max_num = 1


class TVAttributeInline(admin.StackedInline):
    model = TVAttribute
    extra = 0
    max_num = 1


class LaptopAttributeInline(admin.StackedInline):
    model = LaptopAttribute
    extra = 0
    max_num = 1


class ClothingAttributeInline(admin.StackedInline):
    model = ClothingAttribute
    extra = 0
    max_num = 1


class ShoesAttributeInline(admin.StackedInline):
    model = ShoesAttribute
    extra = 0
    max_num = 1


class ApplianceAttributeInline(admin.StackedInline):
    model = ApplianceAttribute
    extra = 0
    max_num = 1


class AutoAttributeInline(admin.StackedInline):
    model = AutoAttribute
    extra = 0
    max_num = 1


class FoodAttributeInline(admin.StackedInline):
    model = FoodAttribute
    extra = 0
    max_num = 1


class FurnitureAttributeInline(admin.StackedInline):
    model = FurnitureAttribute
    extra = 0
    max_num = 1


class BookAttributeInline(admin.StackedInline):
    model = BookAttribute
    extra = 0
    max_num = 1


class HobbyAttributeInline(admin.StackedInline):
    model = HobbyAttribute
    extra = 0
    max_num = 1


class OtherAttributeInline(admin.StackedInline):
    model = OtherAttribute
    extra = 0
    max_num = 1


# ── Category ──
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ["name", "category_type", "parent", "is_active", "order_num"]
    list_filter = ["category_type", "is_active"]


# ── Product ──
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "title", "category", "price", "tax_percent",
        "tax_amount_display", "price_with_tax_display",
        "status", "created_at",
    ]
    list_filter = ["status", "category"]
    search_fields = ["title", "description"]
    list_editable = ["status"]
    readonly_fields = ["tax_amount_display", "price_with_tax_display"]
    actions = ["make_active", "make_rejected"]
    inlines = [
        ProductImageInline,
        PhoneAttributeInline,
        TVAttributeInline,
        LaptopAttributeInline,
        ClothingAttributeInline,
        ShoesAttributeInline,
        ApplianceAttributeInline,
        AutoAttributeInline,
        FoodAttributeInline,
        FurnitureAttributeInline,
        BookAttributeInline,
        HobbyAttributeInline,
        OtherAttributeInline,
    ]

    @admin.display(description="Soliq summasi")
    def tax_amount_display(self, obj):
        return f"{obj.tax_amount:,.2f} so'm"

    @admin.display(description="Narx + soliq")
    def price_with_tax_display(self, obj):
        return f"{obj.price_with_tax:,.2f} so'm"

    @admin.action(description="✅ Tanlangan e'lonlarni AKTIV qilish (publish)")
    def make_active(self, request, queryset):
        updated = queryset.update(status=Product.Status.ACTIVE)
        self.message_user(request, f"{updated} ta e'lon aktiv qilindi.")

    @admin.action(description="❌ Tanlangan e'lonlarni RAD ETISH")
    def make_rejected(self, request, queryset):
        updated = queryset.update(status=Product.Status.REJECTED)
        self.message_user(request, f"{updated} ta e'lon rad etildi.")


# ── Qolgan modellar ──
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ["product", "order", "is_main"]


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ["user", "product", "created_at"]


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ["name"]


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ["name", "hex_code"]


@admin.register(PendingProductEdit)
class PendingProductEditAdmin(admin.ModelAdmin):
    list_display = ["product", "previous_status", "created_at"]
    readonly_fields = ["product", "changes_json", "previous_status", "created_at"]