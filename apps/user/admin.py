from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, SellerProfile


class SellerProfileInline(admin.StackedInline):
    """Seller profili — foydalanuvchi admin sahifasida ko'rinadi"""
    model = SellerProfile
    extra = 0
    max_num = 1
    can_delete = True


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ["username", "id", "email", "role", "telegramID", "is_active", "is_staff", "date_joined"]
    list_filter = ["role", "is_active", "is_staff"]
    list_editable = ["role", "telegramID"]  # telegramID ni list_editable ga qo'shdik
    search_fields = ["username", "email", "phone_number", "id", "telegramID"]
    ordering = ["-id"]  # Yangi foydalanuvchilar birinchi bo'lishi uchun

    fieldsets = UserAdmin.fieldsets + (
        ("Qo'shimcha ma'lumotlar", {
            "fields": ("role", "phone_number", "photo_url", "telegramID"),
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Qo'shimcha ma'lumotlar", {
            "fields": ("role", "phone_number", "telegramID"),
        }),
    )

    inlines = [SellerProfileInline]

    actions = ["make_seller", "make_customer"]

    @admin.action(description="Tanlangan foydalanuvchilarni SOTUVCHI qilish")
    def make_seller(self, request, queryset):
        updated = queryset.update(role=CustomUser.Role.SELLER)
        # Seller profile mavjud bo'lmaganlar uchun yaratish
        for user in queryset.filter(role=CustomUser.Role.SELLER):
            SellerProfile.objects.get_or_create(
                user=user,
                defaults={"shop_name": f"{user.username} do'koni"}
            )
        self.message_user(request, f"{updated} ta foydalanuvchi sotuvchi qilindi.")

    @admin.action(description="Tanlangan foydalanuvchilarni HARIDOR qilish")
    def make_customer(self, request, queryset):
        updated = queryset.update(role=CustomUser.Role.CUSTOMER)
        self.message_user(request, f"{updated} ta foydalanuvchi haridor qilindi.")


@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "shop_name", "region", "district", "rating", "total_sales", "created_at"]
    search_fields = ["shop_name", "user__username"]
    list_filter = ["region"]