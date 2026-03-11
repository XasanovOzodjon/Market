from django.contrib import admin
from .models import Product
from .models import ProductImage
from .models import Favorite
from .models import Category


class PostAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}

admin.site.register(Category, PostAdmin)
admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(Favorite)