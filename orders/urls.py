from django.urls import path
from .views import OrdersView, OrderDetailView

urlpatterns = [

    path("orders/", OrdersView.as_view()),

    path("orders/<int:pk>/", OrderDetailView.as_view()),

]