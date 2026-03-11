from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = 'customer', 'CUSTOMER'
        SELLER = 'seller', 'SELLER'

    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    photo_url = models.URLField(blank=True, null=True)

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.CUSTOMER
    )
    
    
class SellerProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='seller_profile')
    shop_name = models.CharField(max_length=255, unique=True)
    shop_description = models.CharField(max_length=512, blank=True)
    shop_logo = models.ImageField(blank=True, null=True, upload_to='shop_logos/')
    region = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    adress = models.CharField(max_length=255, blank=True)
    rating = models.FloatField(default=0.0)
    total_sales = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    