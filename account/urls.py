from django.urls import path
from .views import TelegramVerificationView, TelegramAuth

from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('get-tg/', TelegramAuth.as_view(), name='get-tg'),
    path('verify-tg/', TelegramVerificationView.as_view(), name='verify-tg'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
