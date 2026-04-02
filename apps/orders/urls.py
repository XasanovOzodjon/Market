from django.urls import path
from .views import OrdersView, OrderDetailView, UserAddressView

urlpatterns = [
    path("orders/", OrdersView.as_view()),
    path("orders/<int:pk>/", OrderDetailView.as_view()),
    path("address/", UserAddressView.as_view()),
]