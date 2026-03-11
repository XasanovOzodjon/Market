from django.db import models
from product.models import Product
from user.models import CustomUser


class Order(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Kutilyapti"
        AGREED = "agreed", "Kelishilgan"
        COMPLETED = "completed", "Sotib olingan"
        CANCELED = "canceled", "Bekor qilingan"

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    buyer = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="buy_orders"
    )

    seller = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="sell_orders"
    )

    final_price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    meeting_location = models.CharField(
        max_length=255,
        blank=True
    )

    meeting_time = models.DateTimeField(
        null=True,
        blank=True
    )

    notes = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def save(self, *args, **kwargs):
        if not self.final_price:
            self.final_price = self.product.price

        if not self.seller:
            self.seller = self.product.seller

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.id} - {self.product.title}"