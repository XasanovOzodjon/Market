from django.urls import path
from .views import UserProfileView, GetDetailsSelerProfile, GetSellerProductsView


urlpatterns = [
    path('users/me', UserProfileView.as_view(), name='user-profile'),
    path('sellers/<int:seller_id>/', GetDetailsSelerProfile.as_view(), name='seller-profile'),
    path('sellers/<int:seller_id>/products/', GetSellerProductsView.as_view(), name='seller-products'),
]
