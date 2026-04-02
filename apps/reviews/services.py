from .models import Review
from django.db.models import Avg
from user.models import SellerProfile


def update_seller_rating(seller):

    avg_rating = Review.objects.filter(
        seller=seller
    ).aggregate(avg=Avg("rating"))["avg"]

    profile = seller.seller_profile

    profile.rating = avg_rating or 0

    profile.save(update_fields=["rating"])