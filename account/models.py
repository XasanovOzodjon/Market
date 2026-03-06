from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = 'customer', 'CUSTOMER'
        SELLER = 'seller', 'SELLER'

    telegram_id = models.BigIntegerField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True)
    photo_url = models.URLField(blank=True, null=True)

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.CUSTOMER
    )