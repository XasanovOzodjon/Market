from django.urls import path

from .views import AddSeller, AdminDashboard

urlpatterns = [
    path('add-seller/', AddSeller.as_view(), name='add-seller'),
]