from django.db import models
from django.utils.text import slugify
from user.models import CustomUser
from django.utils import timezone
from datetime import timedelta
# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey(null=True, blank=True, on_delete=models.SET_NULL, related_name='children', to='self')
    icon = models.ImageField(upload_to="categories/", blank=True)
    description	= models.TextField(max_length=512, blank=True)
    is_active = models.BooleanField(default=True)
    order_num = models.PositiveIntegerField(default=0)
    created_at = models.DateField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
        
from django.db import models
from django.conf import settings


class Product(models.Model):
    def default_expire():
        return timezone.now() + timedelta(days=30)

    class Condition(models.TextChoices):
        NEW = "new", "Yangi"
        IDEAL = "ideal", "Ideal"
        GOOD = "good", "Yaxshi"
        NORMAL = "normal", "Qoniqarli"

    class PriceType(models.TextChoices):
        FIXED = "fixed", "Qat'iy"
        NEGOTIABLE = "negotiable", "Kelishiladi"
        FREE = "free", "Bepul"
        EXCHANGE = "exchange", "Ayirboshlash"

    class Status(models.TextChoices):
        MODERATION = "moderation", "Moderatsiyada"
        ACTIVE = "active", "Aktiv"
        REJECTED = "rejected", "Rad etilgan"
        SOLD = "sold", "Sotilgan"
        ARCHIVED = "archived", "Arxivlangan"

    seller = models.ForeignKey(CustomUser,on_delete=models.CASCADE)

    category = models.ForeignKey(Category,on_delete=models.CASCADE)

    title = models.CharField(max_length=200)
    description = models.TextField()

    condition = models.CharField(max_length=20,choices=Condition.choices)

    price = models.DecimalField(max_digits=12,decimal_places=2)

    price_type = models.CharField(max_length=20,choices=PriceType.choices)

    region = models.CharField(max_length=100)
    district = models.CharField(max_length=100)

    view_count = models.PositiveIntegerField(default=0)
    favorite_count = models.PositiveIntegerField(default=0)

    status = models.CharField(max_length=20,choices=Status.choices,default=Status.MODERATION)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    published_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(default=default_expire)
        
        
from django.db import models


class ProductImage(models.Model):

    product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name="images")

    image = models.ImageField(upload_to="products/")

    order = models.PositiveIntegerField()

    is_main = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.is_main:
            ProductImage.objects.filter(product=self.product, is_main=True).exclude(pk=self.pk).update(is_main=False)
        super().save(*args, **kwargs)
    
    
class Favorite(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "product"]