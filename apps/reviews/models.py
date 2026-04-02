from django.db import models
from user.models import CustomUser
from orders.models import Order


class Review(models.Model):

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="review"
    )

    buyer = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="given_reviews"
    )

    seller = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="received_reviews"
    )

    rating = models.PositiveSmallIntegerField()

    comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review {self.id} - {self.rating}"