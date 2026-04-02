from django.contrib import admin
from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "product", "buyer", "seller", "final_price", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["product__title", "buyer__username", "seller__username"]
    list_editable = ["status"]
    readonly_fields = ["created_at", "updated_at"]
